import pandas as pd
import numpy as np
from typing import Optional



def sentiments_over_time(df: pd.DataFrame, time_col: Optional[str], freq: str = "D"):

    if time_col is None or time_col not in df.columns:

        out = df.groupby("sent_label").size().reset_index(name="count")

        out["period"] = "all"

        return out



    tmp = df.copy()

    ts = pd.to_datetime(tmp[time_col], errors="coerce")



    if freq == "D":

        # midnight of each day

        tmp["period"] = ts.dt.normalize()                 # 2025-10-20 00:00:00

    elif freq == "W":

        tmp["period"] = ts.dt.to_period("W").dt.start_time.dt.normalize()

    elif freq == "M":

        tmp["period"] = ts.dt.to_period("M").dt.start_time.dt.normalize()

    else:

        tmp["period"] = ts.dt.normalize()



    agg = tmp.groupby(["period", "sent_label"]).size().reset_index(name="count")

    totals = agg.groupby("period")["count"].transform("sum")

    agg["pct"] = agg["count"] / totals

    return agg.sort_values("period")





def top_terms_by_period(df: pd.DataFrame, time_col: str, text_col: str, tokenizer=lambda s: s.split(), top_k: int = 10, freq: str = "W"):

    tmp = df.copy()

    if time_col in tmp.columns:

        tmp["period"] = tmp[time_col].dt.to_period(freq).dt.to_timestamp()

    else:

        tmp["period"] = "all"

    rows = []

    for period, g in tmp.groupby("period"):

        tokens = []

        for t in g[text_col].astype(str):

            tokens.extend(tokenizer(t.lower()))

        from collections import Counter

        c = Counter(tokens)

        for tok in list(c.keys()):

            if len(tok) < 3:

                del c[tok]

        for term, cnt in c.most_common(top_k):

            rows.append({"period": period, "term": term, "count": cnt})

    return pd.DataFrame(rows)



def trend_metrics(df: pd.DataFrame, time_col: str, freq: str = "W", roll: int = 3) -> pd.DataFrame:

    """

    Returns period-level trend metrics:

      period, pos, neg, neu, total,

      pos_pct, neg_pct, neu_pct,

      sentiment_index (pos_pct - neg_pct),

      WoW deltas for pos_pct, neg_pct, sentiment_index,

      rolling means for pos_pct, neg_pct, sentiment_index.



    - freq: "D" | "W" | "M"

    - roll: rolling window (periods) for smoothing (default 3)

    """

    if not time_col or time_col not in df.columns:

        return pd.DataFrame()



    tmp = df.copy()

    # tz-safe period bucketing

    ts = pd.to_datetime(tmp[time_col], errors="coerce", utc=True)

    if freq == "D":

        tmp["period"] = ts.dt.floor("D")

    elif freq == "M":

        tmp["period"] = ts.dt.to_period("M").dt.start_time.dt.tz_localize("UTC")

    else:  # weekly default

        tmp["period"] = ts.dt.to_period("W").dt.start_time.dt.tz_localize("UTC")



    # counts per period × label

    counts = (

        tmp.groupby(["period", "sent_label"])

        .size()

        .unstack(fill_value=0)

        .rename(columns={"positive": "pos", "negative": "neg", "neutral": "neu"})

        .sort_index()

    )



    for col in ["pos", "neg", "neu"]:

        if col not in counts.columns:

            counts[col] = 0



    counts["total"] = counts[["pos", "neg", "neu"]].sum(axis=1).astype(int).replace(0, np.nan)



    # percentages

    counts["pos_pct"] = counts["pos"] / counts["total"]

    counts["neg_pct"] = counts["neg"] / counts["total"]

    counts["neu_pct"] = counts["neu"] / counts["total"]



    # sentiment index (range ≈ -1..+1)

    counts["sent_index"] = counts["pos_pct"] - counts["neg_pct"]



    # WoW deltas (or DoD/MoM) of percentages / index

    counts["pos_wow"] = counts["pos_pct"].diff()

    counts["neg_wow"] = counts["neg_pct"].diff()

    counts["index_wow"] = counts["sent_index"].diff()



    # rolling means for smoothing (3-period default)

    if roll and roll > 1:

        counts["pos_pct_ma"] = counts["pos_pct"].rolling(roll, min_periods=1).mean()

        counts["neg_pct_ma"] = counts["neg_pct"].rolling(roll, min_periods=1).mean()

        counts["index_ma"]   = counts["sent_index"].rolling(roll, min_periods=1).mean()

    else:

        counts["pos_pct_ma"] = counts["pos_pct"]

        counts["neg_pct_ma"] = counts["neg_pct"]

        counts["index_ma"]   = counts["sent_index"]



    # tidy up: bring period back as a column, stringify for plotting categories

    out = counts.reset_index()

    out["period_str"] = pd.to_datetime(out["period"], utc=True).dt.tz_convert(None).dt.strftime(

        "%Y-%m-%d" if freq != "M" else "%Y-%m-01"

    )



    # safe fill for display; keep NaNs in pct deltas if you want

    return out
