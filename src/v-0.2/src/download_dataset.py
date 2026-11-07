import argparse, json, re
from pathlib import Path
import requests

DEFAULT_RECORD = "21262042"
FALLBACK_RECORD = "19398358"
KEYWORDS = [
    "temperature_and_power", "temperature", "air_speed", "air_velocity",
    "supplementary_ventilation", "supplementary_hvac", "surrounding_temperatures",
    "layout", "geometry", "measurement_visualization", "3d_model"
]
EXCLUDE = ["readme", "license", "citation"]

def get_record(record_id):
    url = f"https://zenodo.org/api/records/{record_id}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()

def wanted(name):
    n = name.lower()
    if any(x in n for x in EXCLUDE):
        return False
    return any(k in n for k in KEYWORDS)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", default=DEFAULT_RECORD)
    ap.add_argument("--dest", default="data")
    ap.add_argument("--list-only", action="store_true")
    ap.add_argument("--all-scenario-files", action="store_true",
                    help="also include files with scenario/load naming")
    args = ap.parse_args()
    try:
        meta = get_record(args.record)
    except Exception as e:
        if args.record == DEFAULT_RECORD:
            print(f"Could not access record {args.record}: {e}\nTrying fallback {FALLBACK_RECORD}")
            meta = get_record(FALLBACK_RECORD)
        else:
            raise
    files = meta.get("files", [])
    selected = []
    for f in files:
        name = f.get("key", "")
        hit = wanted(name)
        if args.all_scenario_files and any(k in name.lower() for k in ["idle", "25%", "50%", "75%", "100%", "scenario"]):
            hit = True
        if hit:
            selected.append(f)
    print("Record:", meta.get("id"), "|", meta.get("metadata", {}).get("title"))
    print("Version:", meta.get("metadata", {}).get("version"))
    print("Selected files:")
    for f in selected:
        print(f"  {f['key']}  ({f.get('size', 0)/1024/1024:.1f} MiB)")
    if args.list_only:
        return
    dest = Path(args.dest); dest.mkdir(parents=True, exist_ok=True)
    for f in selected:
        target = dest / Path(f["key"]).name
        if target.exists() and target.stat().st_size == f.get("size"):
            print("Already downloaded:", target)
            continue
        url = f.get("links", {}).get("self")
        if not url:
            print("No download URL for", f["key"]); continue
        print("Downloading", f["key"])
        with requests.get(url, stream=True, timeout=(30, 180)) as r:
            r.raise_for_status()
            tmp = target.with_suffix(target.suffix + ".part")
            with open(tmp, "wb") as out:
                for chunk in r.iter_content(8 * 1024 * 1024):
                    if chunk: out.write(chunk)
            tmp.replace(target)
    (dest / "zenodo_record_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("Done. Verify file sizes and checksum on the Zenodo record.")

if __name__ == "__main__":
    main()
