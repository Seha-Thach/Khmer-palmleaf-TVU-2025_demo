from pathlib import Path
from PIL import Image
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"p": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"}

def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def parse_xywh(target):
    m = re.search(r"#xywh=(\d+),(\d+),(\d+),(\d+)", target)
    if not m:
        raise ValueError(f"No xywh in {target}")
    return tuple(map(int, m.groups()))

manifest = load_json(ROOT / "manifest.json")
assert manifest["@context"] == "http://iiif.io/api/presentation/2/context.json"
assert manifest["@type"] == "sc:Manifest"
canvases = manifest["sequences"][0]["canvases"]

report = []
for canvas in canvases:
    kpl = canvas["@id"].split("/")[-1]
    w, h = int(canvas["width"]), int(canvas["height"])
    image_res = canvas["images"][0]["resource"]
    assert int(image_res["width"]) == w
    assert int(image_res["height"]) == h
    
    with Image.open(ROOT / f"{kpl}.jpg") as im:
        assert im.size == (w, h), f"{kpl}.jpg mismatch: {im.size} != {(w,h)}"
        
    root = ET.parse(ROOT / "pagexml" / f"{kpl}.xml").getroot()
    page = root.find(".//p:Page", NS)
    assert int(page.get("imageWidth")) == w
    assert int(page.get("imageHeight")) == h
    
    anno = load_json(ROOT / "annos" / f"{kpl}.json")
    assert anno["@type"] == "sc:AnnotationList"
    assert len(anno["resources"]) == 4
    
    for res in anno["resources"]:
        x, y, bw, bh = parse_xywh(res["on"])
        assert x >= 0 and y >= 0
        assert x + bw <= w, f"{kpl} target outside width"
        assert y + bh <= h, f"{kpl} target outside height"
        
    report.append({"id": kpl, "width": w, "height": h, "annotations": len(anno["resources"])})

out = ROOT / "validation/local_validation_report.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("All local validation checks passed.")
