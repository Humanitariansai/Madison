#!/usr/bin/env python3
# survey_correct_schema.py
# Build a corrected schema + validate + auto-analyze + (optionally) write a cleaned CSV.
# Usage:
#   python survey_correct_schema.py --csv path/to/survey.csv --outdir ./out
#
# Outputs in --outdir:
#   - corrected_schema.json
#   - corrected_schema_summary.md
#   - survey_auto_report.md
#   - issues.csv
#   - cleaned.csv

import argparse, json, re, os
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd

# -----------------------------
# Helpers
# -----------------------------
# Full month names (lowercase)
MONTH_NAMES = [
    "january","february","march","april","may","june",
    "july","august","september","october","november","december"
]

# 3-letter abbreviations (keep exactly 12; handle "sept" separately)
MONTH_ABBR = ["jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]

# Canonical 3-letter form
MONTH_CANON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Build a safe map
MONTH_MAP = {}
MONTH_MAP.update({m: MONTH_CANON[i] for i, m in enumerate(MONTH_NAMES)})
MONTH_MAP.update({a: MONTH_CANON[i] for i, a in enumerate(MONTH_ABBR)})

# Extra alias for 'sept' → 'Sep'
MONTH_MAP["sept"] = "Sep"


DELIMS = [",",";","|"," / "," • "," · "]

def pct_range(series: pd.Series, lower=0.01, upper=0.99) -> Tuple[float, float]:
    s = pd.to_numeric(series, errors="coerce")
    s = s[np.isfinite(s)]
    if len(s) == 0:
        return (np.nan, np.nan)
    lo = float(np.nanpercentile(s, lower*100))
    hi = float(np.nanpercentile(s, upper*100))
    if lo > hi:
        lo, hi = hi, lo
    return lo, hi

def uniq_ratio(series: pd.Series) -> float:
    s = series.dropna().astype(str).str.strip()
    return (s.nunique() / len(s)) if len(s) else 0.0

def mostly_alnum(series: pd.Series, allow=r"A-Za-z0-9\-_") -> float:
    s = series.dropna().astype(str).str.strip()
    if len(s) == 0: return 0.0
    return (s.str.match(rf"^[{allow}]+$")).mean()

def is_all_digits_n(series: pd.Series, n=9) -> float:
    s = series.dropna().astype(str).str.strip()
    if len(s) == 0: return 0.0
    return (s.str.match(rf"^\d{{{n}}}$")).mean()

def month_valid_ratio(series: pd.Series) -> float:
    s = series.dropna().astype(str).str.strip().str.lower()
    if len(s) == 0: return 0.0
    def ok(x):
        if x in MONTH_MAP: return True
        # 1–12 or 01–12
        return re.fullmatch(r"0?[1-9]|1[0-2]", x) is not None
    return s.apply(ok).mean()

def month_normalize(x):
    if pd.isna(x):
        return x
    s = str(x).strip()
    if not s:
        return np.nan
    low = s.lower()
    if low in MONTH_MAP:
        return MONTH_MAP[low]
    # Accept 1–12 or 01–12
    m = re.fullmatch(r"0?([1-9]|1[0-2])", low)
    if m:
        return MONTH_CANON[int(m.group(1)) - 1]
    return np.nan


def split_multi(x: Any) -> List[str]:
    if pd.isna(x): return []
    s = str(x)
    for d in sorted(DELIMS, key=len, reverse=True):
        if d in s:
            return [p.strip() for p in s.split(d) if p.strip()]
    if "," in s:
        return [p.strip() for p in s.split(",") if p.strip()]
    return [s.strip()] if s.strip() else []

def parse_history_months(x: Any) -> float:
    if pd.isna(x): return np.nan
    s = str(x).lower()
    y = re.search(r"(\d+)\s*year", s)
    m = re.search(r"(\d+)\s*month", s)
    yy = int(y.group(1)) if y else 0
    mm = int(m.group(1)) if m else 0
    return yy*12 + mm

def top_uniques(series: pd.Series, k=12) -> List[str]:
    s = series.fillna("(Blank)").astype(str).str.strip()
    vc = s.value_counts().head(k)
    return [str(v) for v in vc.index.tolist()]

# -----------------------------
# Main corrected schema logic
# -----------------------------
def build_corrected_schema(df: pd.DataFrame) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"file": "", "columns": []}

    def add(col, schema_type, **kwargs):
        entry = {"name": col, "schema_type": schema_type}
        entry.update(kwargs)
        schema["columns"].append(entry)

    # ID, Customer_ID as identifiers
    if "ID" in df.columns:
        add("ID", "identifier",
            pattern=r"^[A-Za-z0-9\-_]+$",
            unique_ratio=round(uniq_ratio(df["ID"]), 3),
            alnum_ratio=round(mostly_alnum(df["ID"]), 3))
    if "Customer_ID" in df.columns:
        add("Customer_ID", "identifier",
            pattern=r"^[A-Za-z0-9\-_]+$",
            unique_ratio=round(uniq_ratio(df["Customer_ID"]), 3),
            alnum_ratio=round(mostly_alnum(df["Customer_ID"]), 3))

    # Month dropdown
    if "Month" in df.columns:
        add("Month", "categorical_month",
            allowed_values=MONTH_CANON + [str(i) for i in range(1,13)],
            valid_ratio=round(month_valid_ratio(df["Month"]), 3))

    # Name, Occupation as free text
    if "Name" in df.columns:
        add("Name", "text")
    if "Occupation" in df.columns:
        add("Occupation", "text")

    # Age with enforced bounds 18–60
    if "Age" in df.columns:
        p1, p99 = pct_range(df["Age"])
        add("Age", "integer", min=18, max=60, observed_p1=p1, observed_p99=p99)

    # SSN 9-digit string (not numeric; preserve leading zeros)
    if "SSN" in df.columns:
        add("SSN", "identifier_digits", pattern=r"^\d{9}$",
            digits9_ratio=round(is_all_digits_n(df["SSN"], 9), 3),
            description="9-digit string (leading zeros allowed)")

    # Continuous / integer fields
    cont_float = ["Annual_Income","Monthly_Inhand_Salary","Outstanding_Debt",
                  "Credit_Utilization_Ratio","Total_EMI_per_month",
                  "Amount_invested_monthly","Monthly_Balance"]
    for col in cont_float:
        if col in df.columns:
            lo, hi = pct_range(df[col])
            add(col, "float",
                suggested_min=(max(0.0, lo) if not np.isnan(lo) else 0.0),
                suggested_max=(hi if not np.isnan(hi) else None),
                notes="Non-negative; cap at p99; treat negatives as data issues.")

    def add_nonneg_int(col):
        lo, hi = pct_range(df[col])
        add(col, "integer",
            min=0,
            max=(int(hi) if not np.isnan(hi) else None),
            observed_p1=lo, observed_p99=hi)

    for col in ["Num_Bank_Accounts","Num_Credit_Card","Num_of_Loan",
                "Delay_from_due_date","Num_of_Delayed_Payment","Num_Credit_Inquiries"]:
        if col in df.columns:
            add_nonneg_int(col)

    if "Interest_Rate" in df.columns:
        lo, hi = pct_range(df["Interest_Rate"])
        add("Interest_Rate", "integer",
            min=0,
            max=(int(hi) if not np.isnan(hi) else None),
            observed_p1=lo, observed_p99=hi,
            notes="Treat as % APR. Cap at p99.")

    if "Changed_Credit_Limit" in df.columns:
        lo, hi = pct_range(df["Changed_Credit_Limit"])
        add("Changed_Credit_Limit", "float",
            suggested_min=lo, suggested_max=hi,
            notes="Delta; negatives allowed. Clip to p1–p99.")

    if "Type_of_Loan" in df.columns:
        add("Type_of_Loan", "multi_select",
            delimiter=",", top_values=top_uniques(df["Type_of_Loan"], k=15))

    if "Credit_Mix" in df.columns:
        add("Credit_Mix", "categorical",
            allowed_values=top_uniques(df["Credit_Mix"], k=10))

    if "Payment_of_Min_Amount" in df.columns:
        add("Payment_of_Min_Amount", "categorical",
            allowed_values=top_uniques(df["Payment_of_Min_Amount"], k=10))

    if "Payment_Behaviour" in df.columns:
        add("Payment_Behaviour", "categorical",
            allowed_values=top_uniques(df["Payment_Behaviour"], k=12))

    if "Credit_History_Age" in df.columns:
        months = df["Credit_History_Age"].apply(parse_history_months)
        min_m = int(np.nanmin(months)) if months.notna().any() else None
        max_m = int(np.nanmax(months)) if months.notna().any() else None
        add("Credit_History_Age", "duration_months",
            min_months=min_m, max_months=max_m,
            raw_format_example="e.g., '15 Years and 5 Months'")

    return schema

# -----------------------------
# Validation / Cleaning
# -----------------------------
def validate_and_clean(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    issues = []
    cleaned = df.copy()

    # helper to record an issue
    def add_issue(idx, col, issue, value):
        issues.append({"row": int(idx), "column": col, "issue": issue, "value": value})

    # column-by-column rules
    for c in schema["columns"]:
        name = c["name"]
        stype = c["schema_type"]
        if name not in cleaned.columns:  # skip if missing
            continue

        col = cleaned[name]

        if stype == "identifier":
            pat = re.compile(c.get("pattern", r"^[A-Za-z0-9\-_]+$"))
            for i, v in col.items():
                if pd.isna(v) or str(v).strip() == "":
                    add_issue(i, name, "missing_identifier", v)
                elif not pat.match(str(v).strip()):
                    add_issue(i, name, "invalid_identifier_chars", v)

        elif stype == "identifier_digits":
            pat = re.compile(c.get("pattern", r"^\d{9}$"))
            # Keep as string to preserve leading zeros
            cleaned[name] = col.astype(str).str.strip()
            for i, v in cleaned[name].items():
                if v == "" or (v.lower() in {"nan","none","na"}):
                    add_issue(i, name, "missing_ssn", v)
                elif not pat.match(v):
                    add_issue(i, name, "invalid_ssn_format", v)

        elif stype == "categorical_month":
            cleaned[name] = col.apply(month_normalize)
            for i, v in cleaned[name].items():
                if pd.isna(v):
                    add_issue(i, name, "invalid_or_missing_month", col.iloc[i])

        elif stype == "integer":
            # cast & clip
            vals = pd.to_numeric(col, errors="coerce")
            minv = c.get("min", None)
            maxv = c.get("max", None)
            for i, v in col.items():
                fv = pd.to_numeric(v, errors="coerce")
                if pd.isna(fv):
                    add_issue(i, name, "invalid_integer", v)
                else:
                    if minv is not None and fv < minv:
                        add_issue(i, name, "below_min", fv)
                    if maxv is not None and fv > maxv:
                        add_issue(i, name, "above_max", fv)
            # apply clipping where specified
            if minv is not None: vals = vals.clip(lower=minv)
            if maxv is not None: vals = vals.clip(upper=maxv)
            cleaned[name] = vals.round().astype("Int64")

        elif stype == "float":
            vals = pd.to_numeric(col, errors="coerce")
            smin = c.get("suggested_min", None)
            smax = c.get("suggested_max", None)
            # non-negative note: if suggested_min is given, use it; else 0
            if "notes" in c and "Non-negative" in c["notes"]:
                nonneg_min = 0.0 if smin is None else max(0.0, smin)
                smin = nonneg_min
            if smin is not None: vals = vals.clip(lower=smin)
            if smax is not None: vals = vals.clip(upper=smax)
            cleaned[name] = vals

        elif stype == "multi_select":
            # leave raw text; can also explode later if needed
            delim = c.get("delimiter", ",")
            # basic check: at least one item non-empty
            for i, v in col.items():
                if pd.isna(v) or str(v).strip() == "":
                    add_issue(i, name, "missing_multi_select", v)

        elif stype == "categorical":
            allowed = set([a.strip() for a in c.get("allowed_values", []) if a is not None])
            if allowed:
                for i, v in col.items():
                    sv = str(v).strip() if not pd.isna(v) else ""
                    if sv == "":
                        add_issue(i, name, "missing_category", v)
                    elif sv not in allowed:
                        add_issue(i, name, "unknown_category", v)

        elif stype == "text":
            # no strict validation, record blanks
            for i, v in col.items():
                if pd.isna(v) or str(v).strip() == "":
                    add_issue(i, name, "missing_text", v)

        elif stype == "duration_months":
            months = col.apply(parse_history_months)
            cleaned[name + "_Months"] = months
            if months.notna().any():
                minm, maxm = months.min(), months.max()
                min_rule, max_rule = c.get("min_months"), c.get("max_months")
                # Not clipping here; just record issues if unparsable
            for i, v in col.items():
                if pd.isna(v) or str(v).strip() == "":
                    add_issue(i, name, "missing_credit_history_age", v)
                elif pd.isna(parse_history_months(v)):
                    add_issue(i, name, "unparsable_credit_history_age", v)

    issues_df = pd.DataFrame(issues)
    return cleaned, issues_df

# -----------------------------
# Auto-report
# -----------------------------
def make_auto_report(df: pd.DataFrame, schema: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Auto Survey Analysis Report\n")
    lines.append(f"**Rows:** {len(df):,}  **Columns:** {df.shape[1]}\n")

    # type counts
    type_counts = {}
    for c in schema["columns"]:
        t = c["schema_type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    lines.append("## Detected Types (from corrected schema)")
    for k,v in sorted(type_counts.items(), key=lambda x: x[0]):
        lines.append(f"- {k}: {v}")
    lines.append("")

    # Quick per-type summaries
    def add_table(title, rows: List[Dict[str, Any]]):
        if not rows: return
        lines.append(f"### {title}")
        if rows:
            cols = list(rows[0].keys())
            # markdown table
            lines.append("| " + " | ".join(cols) + " |")
            lines.append("| " + " | ".join(["---"]*len(cols)) + " |")
            for r in rows:
                lines.append("| " + " | ".join(str(r.get(c,"")) for c in cols) + " |")
        lines.append("")

    # numeric summary
    num_rows = []
    for c in schema["columns"]:
        if c["schema_type"] in ("integer","float"):
            col = c["name"]
            vals = pd.to_numeric(df[col], errors="coerce")
            clean = vals.dropna()
            if len(clean) > 0:
                num_rows.append({
                    "Column": col,
                    "Type": c["schema_type"],
                    "Non-missing": int(len(clean)),
                    "Mean": round(float(np.nanmean(clean)), 3),
                    "Median": round(float(np.nanmedian(clean)), 3),
                    "Min": round(float(np.nanmin(clean)), 3),
                    "P90": round(float(np.nanpercentile(clean,90)), 3),
                    "Max": round(float(np.nanmax(clean)), 3),
                })
            else:
                num_rows.append({"Column": col, "Type": c["schema_type"], "Non-missing": 0})
    add_table("Numeric Columns Summary", num_rows)

    # categorical summary
    cat_rows = []
    for c in schema["columns"]:
        if c["schema_type"] in ("categorical","categorical_month"):
            col = c["name"]
            counts = df[col].fillna("(Blank)").astype(str).str.strip().value_counts().head(12)
            cat_rows.append({
                "Column": col,
                "Top Values": "; ".join([f"{k}:{v}" for k,v in counts.items()])
            })
    add_table("Categorical Columns Summary", cat_rows)

    # text summary
    text_rows = []
    for c in schema["columns"]:
        if c["schema_type"] == "text":
            col = c["name"]
            s = df[col].astype(str)
            text_rows.append({
                "Column": col,
                "Unique": int(s.nunique(dropna=True)),
                "Avg Length": round(float(s.str.len().mean()), 2)
            })
    add_table("Text Columns Summary", text_rows)

    return "\n".join(lines)

# -----------------------------
# CLI
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to survey CSV")
    ap.add_argument("--outdir", default=".", help="Output directory")
    ap.add_argument("--no-clean", action="store_true",
                    help="Do not write cleaned.csv (only schema, report, issues)")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path, dtype=str)

    # Build corrected schema per requirements
    schema = build_corrected_schema(df)
    schema["file"] = csv_path.name

    # Validate and clean
    cleaned, issues = validate_and_clean(df, schema)

    # Save schema + summary
    (outdir / "corrected_schema.json").write_text(json.dumps(schema, indent=2))
    # human summary
    summary_lines = ["# Corrected Survey Schema (Summary)\n"]
    for c in schema["columns"]:
        line = f"- **{c['name']}** → {c['schema_type']}"
        for k in ["pattern","min","max","suggested_min","suggested_max","min_months","max_months","unique_ratio","alnum_ratio","digits9_ratio","delimiter","valid_ratio"]:
            if k in c and c[k] is not None:
                line += f", {k}: {c[k]}"
        if "allowed_values" in c:
            line += f", allowed: {c['allowed_values']}"
        if "notes" in c:
            line += f" — {c['notes']}"
        summary_lines.append(line)
    (outdir / "corrected_schema_summary.md").write_text("\n".join(summary_lines))

    # Save issues
    if not issues.empty:
        issues.to_csv(outdir / "issues.csv", index=False)
    else:
        pd.DataFrame(columns=["row","column","issue","value"]).to_csv(outdir / "issues.csv", index=False)

    # Save cleaned (unless disabled)
    if not args.no_clean:
        cleaned.to_csv(outdir / "cleaned.csv", index=False)

    # Auto-report on cleaned (so stats reflect normalized values)
    report = make_auto_report(cleaned, schema)
    (outdir / "survey_auto_report.md").write_text(report)

    print(f"\nDone.\n"
          f"- corrected_schema.json\n"
          f"- corrected_schema_summary.md\n"
          f"- issues.csv  (validation issues)\n"
          f"- cleaned.csv (normalized/clipped) {'[SKIPPED]' if args.no_clean else ''}\n"
          f"- survey_auto_report.md\n"
          f"in: {outdir.resolve()}\n")

if __name__ == "__main__":
    main()