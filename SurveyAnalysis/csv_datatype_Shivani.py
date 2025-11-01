#!/usr/bin/env python3
import argparse
import json
import math
import re
from typing import Dict

import numpy as np
import pandas as pd

LIKERT_LABELS = {
    "strongly disagree","disagree","neutral","agree","strongly agree",
    "somewhat agree","somewhat disagree","totally disagree","totally agree"
}
DELIMS = [",",";","|"," / "," • "," · "]

def to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def pct_true(mask: pd.Series) -> float:
    if mask.size == 0: return 0.0
    return float(mask.mean())

def looks_boolean(s: pd.Series) -> bool:
    nonnull = s.dropna().astype(str).str.strip().str.lower()
    if nonnull.empty: return False
    mapped = nonnull.replace({"y":"yes","n":"no","true":"yes","false":"no","1":"yes","0":"no"})
    uniques = set(mapped.unique())
    return len(uniques) <= 2 and uniques.issubset({"yes","no"})

def numeric_profile(s: pd.Series):
    nums = to_num(s).dropna()
    if nums.empty:
        return None
    return {
        "min": float(nums.min()),
        "max": float(nums.max()),
        "unique": int(nums.nunique()),
        "count": int(nums.size),
        "all_int": bool(np.all(np.isclose(nums % 1, 0)))
    }

def looks_likert(s: pd.Series) -> bool:
    prof = numeric_profile(s)
    if prof and prof["all_int"] and prof["unique"] in {5,7} and prof["min"] in {0.0,1.0}:
        return True
    nonnull = s.dropna().astype(str).str.strip().str.lower()
    if nonnull.empty: return False
    return pct_true(nonnull.apply(lambda x: any(lbl in x for lbl in LIKERT_LABELS))) >= 0.5

def looks_rating_or_nps(s: pd.Series):
    prof = numeric_profile(s)
    if not prof: return False, None
    if prof["all_int"] and 0.0 <= prof["min"] and prof["max"] <= 10.0:
        if abs(prof["min"]-0.0) < 1e-9 and abs(prof["max"]-10.0) < 1e-9:
            return True, "NPS (0–10) or 0–10 rating"
        return True, "Rating (bounded integer scale ≤10)"
    return False, None

def looks_slider(s: pd.Series) -> bool:
    prof = numeric_profile(s)
    if not prof: return False
    if not prof["all_int"] and prof["unique"] >= max(10, int(0.1*prof["count"])):
        return True
    if prof["min"] >= 0.0 and prof["max"] <= 100.0 and not prof["all_int"] and prof["unique"] >= 20:
        return True
    return False

def looks_multiselect(s: pd.Series):
    nonnull = s.dropna().astype(str)
    if nonnull.empty: return False, None
    for d in DELIMS:
        if pct_true(nonnull.str.contains(re.escape(d))) >= 0.3:
            return True, f"delimiter='{d.strip()}'"
    return False, None

def looks_categorical_single(s: pd.Series) -> bool:
    nonnull = s.dropna().astype(str)
    if nonnull.empty: return False
    if looks_boolean(s): return False
    k = nonnull.nunique()
    n = nonnull.size
    try_num = pd.to_numeric(nonnull, errors="coerce")
    if try_num.notna().mean() >= 0.9:
        return False
    return 2 <= k <= min(15, max(3, n//10))

def looks_date(s: pd.Series) -> bool:
    nonnull = s.dropna().astype(str).str.strip()
    if nonnull.empty: return False
    parsed = pd.to_datetime(nonnull, errors="coerce", infer_datetime_format=True)
    return parsed.notna().mean() >= 0.9

def looks_open_text(s: pd.Series) -> bool:
    nonnull = s.dropna().astype(str).str.strip()
    if nonnull.empty: return False
    longish = nonnull.str.len() >= 15
    has_letters = nonnull.str.contains(r"[A-Za-z]")
    uniq_frac = nonnull.nunique() / max(1, nonnull.size)
    return float((longish | has_letters).mean()) >= 0.6 and uniq_frac >= 0.5

def infer_type(col: str, s: pd.Series) -> Dict[str,str]:
    if looks_boolean(s):
        return {"column": col, "type": "Boolean/Binary", "details": ""}
    ms, note = looks_multiselect(s)
    if ms:
        return {"column": col, "type": "Multiple Choice (Multi-Select)", "details": note or ""}
    if looks_likert(s):
        return {"column": col, "type": "Likert (5- or 7-point)", "details": ""}
    flag, note = looks_rating_or_nps(s)
    if flag:
        return {"column": col, "type": "Rating / NPS", "details": note or ""}
    if looks_slider(s):
        return {"column": col, "type": "Slider (continuous)", "details": ""}
    if looks_date(s):
        return {"column": col, "type": "Date/Datetime", "details": ""}
    prof = numeric_profile(s)
    if prof:
        if prof["all_int"]:
            return {"column": col, "type": "Integer", "details": f"range [{prof['min']},{prof['max']}], {prof['unique']} uniques"}
        else:
            return {"column": col, "type": "Float", "details": f"range [{prof['min']},{prof['max']}], {prof['unique']} uniques"}
    if looks_categorical_single(s):
        return {"column": col, "type": "Multiple Choice (Single-Select/Categorical)", "details": ""}
    if looks_open_text(s):
        return {"column": col, "type": "Open-Ended (Free Text)", "details": ""}
    return {"column": col, "type": "Unknown", "details": ""}

def main():
    ap = argparse.ArgumentParser(description="Infer likely data types for each column of a CSV (survey-friendly heuristics).")
    ap.add_argument("--csv", required=True, help="Path to CSV")
    ap.add_argument("--sep", default=",", help="Field separator (default ,)")
    ap.add_argument("--max-rows", type=int, default=200000, help="Optional row cap")
    ap.add_argument("--json", action="store_true", help="Also print JSON")
    args = ap.parse_args()

    df = pd.read_csv(args.csv, sep=args.sep, nrows=args.max_rows, dtype=str)
    results = [infer_type(c, df[c]) for c in df.columns]

    print("\n=== CSV Data Type Inference ===\n")
    print(f"File: {args.csv}  Rows: {len(df)}  Columns: {len(df.columns)}\n")
    for r in results:
        det = f" — {r['details']}" if r.get("details") else ""
        print(f" • {r['column']}: {r['type']}{det}")
    if args.json:
        print("\n=== JSON ===")
        print(json.dumps({ "file": args.csv, "columns": results }, indent=2))

if __name__ == "__main__":
    main()
