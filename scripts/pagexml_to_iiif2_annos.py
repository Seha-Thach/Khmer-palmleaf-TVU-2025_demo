from pathlib import Path
import csv
import json
import re
import xml.etree.ElementTree as ET

NS = {"p": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"}
ROOT = Path(__file__).resolve().parents[1]
BASE = "https://seha-thach.github.io/Khmer-palmleaf-TVU-2025_demo"

def nums(points):
    return list(map(int, re.findall(r"-?\d+", points or "")))

def bbox_from_points(points, pad_x=0, pad_y=0, width=None, height=None):
    n = nums(points)
    xs, ys = n[0::2], n[1::2]
    if not xs or not ys:
        return None
    x0, x1 = min(xs) - pad_x, max(xs) + pad_x
    y0, y1 = min(ys) - pad_y, max(ys) + pad_y
    x0 = max(0, x0)
    y0 = max(0, y0)
    if width is not None:
        x1 = min(width, x1)
    if height is not None:
        y1 = min(height, y1)
    return x0, y0, max(1, x1 - x0), max(1, y1 - y0)

def load_overrides():
    path = ROOT / "metadata/manual_bbox_overrides.csv"
    data = {}
    if not path.exists():
        return data
    for r in csv.DictReader(open(path, encoding="utf-8")):
        data[(r["kpl_id"], r["line_id"])] = (
            int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"])
        )
    return data

def within_canvas(x, y, w, h, width, height):
    return x >= 0 and y >= 0 and x + w <= width and y + h <= height

overrides = load_overrides()

for xml_path in sorted((ROOT / "pagexml").glob("KPL_*.xml")):
    kpl = xml_path.stem
    root = ET.parse(xml_path).getroot()
    page = root.find(".//p:Page", NS)
    width, height = int(page.get("imageWidth")), int(page.get("imageHeight"))
    
    resources = []
    diagnostics = []
    
    for idx, line in enumerate(root.findall(".//p:TextLine", NS), start=1):
        line_id = line.get("id") or f"L{idx:03d}"
        text = line.findtext(".//p:Unicode", "", NS).strip()
        if not text:
            continue
            
        override = overrides.get((kpl, line_id))
        if override:
            x, y, w, h = override
            method = "manual_override"
        else:
            coords = line.find("p:Coords", NS)
            baseline = line.find("p:Baseline", NS)
            if coords is not None and coords.get("points"):
                x, y, w, h = bbox_from_points(coords.get("points"), pad_x=0, pad_y=0, width=width, height=height)
                method = "coords_polygon_bbox"
            elif baseline is not None and baseline.get("points"):
                x, y, w, h = bbox_from_points(baseline.get("points"), pad_x=35, pad_y=45, width=width, height=height)
                method = "baseline_fallback"
            else:
                raise ValueError(f"{kpl} {line_id}: no Coords or Baseline available")
                
        if not within_canvas(x, y, w, h, width, height):
            raise ValueError(f"{kpl} {line_id}: bbox outside canvas: {(x,y,w,h)} vs {(width,height)}")
            
        anno_id = f"{BASE}/anno/{kpl}-L{idx:03d}"
        canvas_uri = f"{BASE}/canvas/{kpl}"
        target = f"{canvas_uri}#xywh={x},{y},{w},{h}"
        
        resources.append({
            "@id": anno_id,
            "@type": "oa:Annotation",
            "motivation": "sc:supplementing",
            "resource": {
                "@type": "cnt:ContentAsText",
                "format": "text/plain",
                "chars": text,
                "language": "km-Khmr"
            },
            "on": target
        })
        
        diagnostics.append({
            "line_id": line_id,
            "target": target,
            "bbox_method": method,
            "text_length": len(text)
        })
        
    anno_list = {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@id": f"{BASE}/annos/{kpl}.json",
        "@type": "sc:AnnotationList",
        "resources": resources
    }
    
    out = ROOT / "annos" / f"{kpl}.json"
    out.write_text(json.dumps(anno_list, ensure_ascii=False, indent=2), encoding="utf-8")
    
    diag = ROOT / "validation" / f"{kpl}_annotation_generation_report.json"
    diag.parent.mkdir(exist_ok=True)
    diag.write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8")

print("Annotation Lists generated.")
