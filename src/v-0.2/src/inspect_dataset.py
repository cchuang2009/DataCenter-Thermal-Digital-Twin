import argparse, json, re
from pathlib import Path
import pandas as pd

ID_TOKENS = ("sensor", "point", "probe", "port", "measurement", "channel", "id")
X_TOKENS = ("x", "x_m", "x_mm", "x-coordinate", "x coordinate")
Y_TOKENS = ("y", "y_m", "y_mm", "y-coordinate", "y coordinate")
Z_TOKENS = ("z", "z_m", "z_mm", "z-coordinate", "z coordinate")

def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).strip().lower()).strip("_")

def find_col(cols, tokens):
    normed = {c: norm(c) for c in cols}
    for c, n in normed.items():
        if n in tokens: return c
    for c, n in normed.items():
        if any(t in n for t in tokens if len(t) > 1): return c
    return None

def inspect_csv(path, chunksize=50000):
    result = {"file": path.name, "size_bytes": path.stat().st_size}
    try:
        first = pd.read_csv(path, nrows=100, low_memory=False)
        result["columns"] = [{"name": str(c), "dtype": str(first[c].dtype)} for c in first.columns]
        result["sample_rows"] = first.head(5).replace({float("nan"): None}).to_dict("records")
        result["rows_scanned"] = 0
        # scan chunks for approximate count and time/id unique examples without retaining full data
        ids = set()
        for chunk in pd.read_csv(path, chunksize=chunksize, low_memory=False):
            result["rows_scanned"] += len(chunk)
            id_col = find_col(chunk.columns, ID_TOKENS)
            if id_col:
                ids.update(map(str, chunk[id_col].dropna().unique()[:5000]))
        result["candidate_id_column"] = id_col if len(first.columns) else None
        result["candidate_ids_sample"] = sorted(ids)[:200]
    except Exception as e:
        result["error"] = str(e)
    return result

def inspect_excel(path):
    xls = pd.ExcelFile(path)
    out = {"file": path.name, "sheets": []}
    candidates = []
    for sheet in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet, nrows=500)
        cols = list(df.columns)
        idc = find_col(cols, ID_TOKENS)
        xc, yc, zc = find_col(cols, X_TOKENS), find_col(cols, Y_TOKENS), find_col(cols, Z_TOKENS)
        out["sheets"].append({
            "sheet": sheet, "columns": [str(c) for c in cols],
            "rows_preview": len(df), "candidate_id": str(idc) if idc else None,
            "candidate_xyz": [str(x) if x else None for x in (xc,yc,zc)],
            "preview": df.head(5).astype(str).to_dict("records")
        })
        if idc:
            for _, row in df.iterrows():
                sid = row.get(idc)
                if pd.isna(sid): continue
                candidates.append({
                    "sensor_id": str(sid).strip(),
                    "measurement_port": str(row.get(find_col(cols, ("power_use_measurement_port","power_measurement_port","measurement_port","port")), "")),
                    "x_m": row.get(xc) if xc else None,
                    "y_m": row.get(yc) if yc else None,
                    "z_m": row.get(zc) if zc else None,
                    "coordinate_source": f"{path.name}:{sheet}" if xc and yc and zc else "",
                    "review_status": "needs_review"
                })
    return out, candidates

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="outputs/inspection")
    args = ap.parse_args()
    data_dir, out_dir = Path(args.data_dir), Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_reports = []
    for p in sorted(data_dir.glob("*.csv")):
        if p.name.startswith("sensor_xyz"):
            continue
        print("Inspecting CSV:", p.name)
        csv_reports.append(inspect_csv(p))
    excel_reports, candidates = [], []
    for p in sorted(data_dir.glob("*.xlsx")):
        print("Inspecting workbook:", p.name)
        rep, rows = inspect_excel(p)
        excel_reports.append(rep); candidates.extend(rows)
    (out_dir/"csv_schema_report.json").write_text(json.dumps(csv_reports, indent=2, default=str), encoding="utf-8")
    (out_dir/"excel_workbook_report.json").write_text(json.dumps(excel_reports, indent=2, default=str), encoding="utf-8")
    # de-duplicate by ID, preserve first workbook row
    seen, unique = set(), []
    for row in candidates:
        if row["sensor_id"] not in seen:
            seen.add(row["sensor_id"]); unique.append(row)
    pd.DataFrame(unique, columns=["sensor_id","measurement_port","x_m","y_m","z_m","coordinate_source","review_status"]).to_csv(
        out_dir/"sensor_xyz_template.csv", index=False)
    print("Reports:", out_dir)
    print("Workbook ID candidates:", len(unique))
    if unique and not any(all(row.get(k) is not None and str(row.get(k)) != "nan" for k in ("x_m","y_m","z_m")) for row in unique):
        print("NOTE: Workbook appears not to contain complete XYZ coordinates. Reconcile IDs with the official CAD drawing.")
if __name__ == "__main__":
    main()
