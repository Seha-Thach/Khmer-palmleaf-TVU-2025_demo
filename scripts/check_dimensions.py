from pathlib import Path
from PIL import Image
import csv
import json
import xml.etree.ElementTree as ET

NS = {"p": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"}
ROOT = Path(__file__).resolve().parents[1]

def page_dims(xml_path):
    root = ET.parse(xml_path).getroot()
    page = root.find(".//p:Page", NS)
    return int(page.get("imageWidth")), int(page.get("imageHeight"))

rows = list(csv.DictReader(open(ROOT / "metadata/kpl_dimensions.csv", encoding="utf-8")))
report = []
ok = True

for r in rows:
    kpl = r["kpl_id"]
    expected = (int(r["width"]), int(r["height"]))
    jpg_path = ROOT / r["jpg_file"]
    xml_path = ROOT / r["pagexml_file"]
    
    with Image.open(jpg_path) as im:
        jpg_dims = im.size
        
    xml_dims = page_dims(xml_path)
    
    status = {
        "id": kpl,
        "expected": expected,
        "jpg": jpg_dims,
        "pagexml": xml_dims,
        "jpg_matches": jpg_dims == expected,
        "pagexml_matches": xml_dims == expected
    }
    
    if not (status["jpg_matches"] and status["pagexml_matches"]):
        ok = False
        
    report.append(status)

out = ROOT / "validation/pagexml_image_dimension_report.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

if not ok:
    raise SystemExit("Dimension mismatch detected. See validation/pagexml_image_dimension_report.json")

print("All image/PAGE-XML dimensions match metadata/kpl_dimensions.csv")
