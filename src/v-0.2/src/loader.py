import pandas as pd
import numpy as np
import re

def norm(s):
    return re.sub(r"[^a-z0-9]+","_",str(s).lower()).strip("_")

def guess_col(cols, tokens):
    for c in cols:
        n=norm(c)
        if n in tokens: return c
    for c in cols:
        n=norm(c)
        if any(t in n for t in tokens): return c
    return None

def load_preview(path, nrows=250000):
    return pd.read_csv(path, nrows=nrows, low_memory=False)

def to_long(df, timestamp_col, temperature_col, sensor_col=None):
    if sensor_col:
        out=df[[timestamp_col,sensor_col,temperature_col]].copy()
        out.columns=["timestamp","sensor_id","temperature"]
    else:
        out=df[[timestamp_col,temperature_col]].copy()
        out=out.melt(id_vars=[timestamp_col], var_name="sensor_id", value_name="temperature")
        out=out.rename(columns={timestamp_col:"timestamp"})
    out["temperature"]=pd.to_numeric(out["temperature"],errors="coerce")
    out=out.dropna(subset=["temperature","sensor_id"])
    out["sensor_id"]=out["sensor_id"].astype(str).str.strip()
    return out
