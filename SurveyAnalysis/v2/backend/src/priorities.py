# src/priorities.py

from __future__ import annotations

from typing import List, Dict, Optional

from dataclasses import dataclass

import pandas as pd

import numpy as np





@dataclass

class ThemeStats:

    keyphrase: str

    count: int

    neg_share: float

    recency: float

    trend: float

    effort: float

    priority: float





def _get_sentiment_series(df: pd.DataFrame) -> pd.Series:

    """

    Return a numeric sentiment series in [-1, 1].

    Prefers 'sent_compound' if present, else maps 'sent_label'.

    """

    if "sent_compound" in df.columns:

        return df["sent_compound"].astype(float).fillna(0.0)



    if "sent_label" in df.columns:

        mapping = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}

        return df["sent_label"].map(mapping).fillna(0.0)



    # fallback: all neutral

    return pd.Series(0.0, index=df.index)





def _normalize_recency(ts: pd.Series) -> pd.Series:

    """

    Given a datetime series, return recency scores in [0,1]:

    newest → 1, oldest → 0. If all equal or empty, 0.

    """

    if ts.isna().all():

        return pd.Series(0.0, index=ts.index)



    t_min = ts.min()

    t_max = ts.max()

    if t_min == t_max:

        return pd.Series(0.0, index=ts.index)



    span = (t_max - t_min).total_seconds()

    return (ts - t_min).dt.total_seconds() / span





def _theme_mask(df: pd.DataFrame, text_col: str, theme: str) -> pd.Series:

    """

    Simple substring match: does this row's text mention the theme?

    """

    return df[text_col].astype(str).str.contains(theme, case=False, na=False)









def compute_theme_priorities(

    df: pd.DataFrame,

    themes: List[str],

    text_col: str,

    time_col: Optional[str] = None,

    effort_map: Optional[Dict[str, float]] = None,

    freq: str = "W",        # for trend (weekly by default)

) -> pd.DataFrame:

    """

    Compute a priority score per theme.



    Columns returned:

      - keyphrase

      - count       (how often theme appears)

      - neg_share   (share of mentions that are negative)

      - recency     (0..1, newer mentions -> higher)

      - trend       (-1..1-ish, is it getting worse?)

      - effort      (0.1..1.0, higher = harder to fix)

      - priority    (higher = fix sooner; negative-heavy, frequent, recent, worsening, low-effort)



    priority ~ count * neg_share * recency_boost * trend_boost / effort

    """

    if not themes:

        return pd.DataFrame(columns=["keyphrase","count","neg_share","recency","trend","effort","priority"])



    themes = [t for t in themes if isinstance(t, str) and t.strip()]

    if not themes:

        return pd.DataFrame(columns=["keyphrase","count","neg_share","recency","trend","effort","priority"])



    sent = _get_sentiment_series(df)

    has_time = bool(time_col and time_col in df.columns)



    if has_time:

        time = pd.to_datetime(df[time_col], errors="coerce", utc=True)

        time = time.dt.tz_convert(None)

    else:

        time = pd.Series(pd.NaT, index=df.index)



    stats: List[ThemeStats] = []



    # Precompute global recency scores (per row)

    recency_row = _normalize_recency(time) if has_time else pd.Series(0.0, index=df.index)

    

    # Precompute negative mask for faster access

    neg_mask = (sent < 0)



    for theme in themes:

        mask = _theme_mask(df, text_col, theme)

        if not mask.any():

            continue



        # --- count ---

        count = int(mask.sum())



        # --- neg_share (vectorized) ---

        neg_count = int((neg_mask & mask).sum())

        neg_share = float(neg_count / count) if count > 0 else 0.0



        # --- recency (mean of recency scores for rows mentioning theme) ---

        if has_time:

            rec = float(recency_row[mask].mean())

        else:

            rec = 0.0



        # --- trend: is theme getting worse over time? ---

        if has_time:

            # Vectorized: filter by mask, then resample

            theme_time = time[mask]

            theme_neg = neg_mask[mask]

            if theme_time.notna().any():

                tmp = pd.DataFrame({"time": theme_time, "neg": theme_neg.astype(int)})

                tmp = tmp.dropna(subset=["time"])

                if not tmp.empty:

                    tmp = tmp.set_index("time").resample(freq).sum()

                    if len(tmp) >= 2:

                        # compare last vs previous negative counts

                        last = tmp["neg"].iloc[-1]

                        prev = tmp["neg"].iloc[-2]

                        denom = max(prev, 1)

                        raw = (last - prev) / denom   # can be negative or positive

                        trend_val = float(np.clip(raw, -1.0, 1.0))

                    else:

                        trend_val = 0.0

                else:

                    trend_val = 0.0

            else:

                trend_val = 0.0

        else:

            trend_val = 0.0



        # --- effort ---

        if effort_map is not None:

            eff = float(effort_map.get(theme, 0.5))

        else:

            eff = 0.5  # default medium effort



        eff = float(np.clip(eff, 0.1, 1.0))   # avoid divide-by-zero and extremes



        # --- priority formula ---

        neg_impact = count * neg_share



        # recency boost: 1..2

        recency_boost = 1.0 + rec



        # trend boost: 0.5..1.5 (worse -> >1, better -> <1)

        trend_boost = 1.0 + float(np.clip(trend_val, -0.5, 0.5))



        priority = neg_impact * recency_boost * trend_boost / eff



        stats.append(

            ThemeStats(

                keyphrase=theme,

                count=count,

                neg_share=neg_share,

                recency=rec,

                trend=trend_val,

                effort=eff,

                priority=float(priority),

            )

        )



    if not stats:

        return pd.DataFrame(columns=["keyphrase","count","neg_share","recency","trend","effort","priority"])



    df_out = pd.DataFrame([s.__dict__ for s in stats])

    # For convenience, also add neg_impact for UI sorting/debug

    df_out["neg_impact"] = df_out["count"] * df_out["neg_share"]

    # Sort by priority descending by default

    df_out = df_out.sort_values("priority", ascending=False).reset_index(drop=True)

    return df_out
