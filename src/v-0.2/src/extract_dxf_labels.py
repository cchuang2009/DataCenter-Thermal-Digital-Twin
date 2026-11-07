import argparse, csv
from pathlib import Path
try:
    import ezdxf
except ImportError:
    raise SystemExit("Install optional dependency first: pip install ezdxf")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--out", default="outputs/dxf_entities.csv")
    a=ap.parse_args()
    doc=ezdxf.readfile(a.dxf); msp=doc.modelspace()
    rows=[]
    for e in msp:
        typ=e.dxftype()
        row={"entity_type":typ,"layer":getattr(e.dxf,"layer","")}
        if typ in ("TEXT","MTEXT"):
            row["text"]=e.dxf.text if typ=="TEXT" else e.text
            p=e.dxf.insert; row.update(x=p.x,y=p.y,z=p.z)
        elif typ=="POINT":
            p=e.dxf.location; row.update(x=p.x,y=p.y,z=p.z)
        elif typ=="INSERT":
            p=e.dxf.insert; row.update(block=e.dxf.name,x=p.x,y=p.y,z=p.z)
        else:
            continue
        rows.append(row)
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=sorted({k for r in rows for k in r}))
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} text/point/block entities to {out}")
if __name__=="__main__": main()
