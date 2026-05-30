from pathlib import Path
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://seha-thach.github.io/Khmer-palmleaf-TVU-2025_demo"
SEARCH = "https://bitter-boat-ceb5.seha-tvu.workers.dev/search"

rows = list(csv.DictReader(open(ROOT / "metadata/kpl_dimensions.csv", encoding="utf-8")))

manifest = {
  "@context": "http://iiif.io/api/presentation/2/context.json",
  "@id": f"{BASE}/manifest.json",
  "@type": "sc:Manifest",
  "label": "Khmer Palm-Leaf Manuscripts in Southern Vietnam — Demo (5 Recto Leaves)",
  "description": (
    "This IIIF-based methodological proof of concept presents five Khmer palm-leaf "
    "manuscript images with line-level PAGE-XML-derived annotations, manually curated "
    "text layers, translation resources, and IIIF Content Search API support."
  ),
  "viewingHint": "paged",
  "attribution": "Seha Thach — Tra Vinh University, 2025.",
  "license": "https://creativecommons.org/licenses/by/4.0/",
  "service": [{
    "@context": "http://iiif.io/api/search/1/context.json",
    "@id": SEARCH,
    "profile": "http://iiif.io/api/search/1/search"
  }],
  "rendering": [
    {
      "@id": f"{BASE}/text/translations.html",
      "label": "Translations",
      "format": "text/html"
    },
    {
      "@id": f"{BASE}/text/translations.json",
      "label": "Translations (JSON)",
      "format": "application/json"
    }
  ],
  "seeAlso": [
    {
      "@id": "https://zenodo.org/records/17523995",
      "label": "Zenodo DOI record",
      "format": "text/html"
    },
    {
      "@id": "https://archive.org/details/lb-01-003r_202511",
      "label": "Internet Archive source-image record",
      "format": "text/html"
    },
    {
      "@id": "https://github.com/Seha-Thach/Khmer-palmleaf-TVU-2025_demo",
      "label": "GitHub repository",
      "format": "text/html"
    }
  ],
  "metadata": [
    {"label": "Creator", "value": "Seha Thach"},
    {"label": "Institution", "value": "Tra Vinh University"},
    {"label": "Date", "value": "2025-11-05"},
    {"label": "Language", "value": "km-Khmr; pi-Khmr"},
    {"label": "Script", "value": "Khmr"},
    {"label": "Spatial", "value": "geonames:1566166"},
    {"label": "License", "value": "CC BY 4.0"},
    {"label": "Attribution", "value": "Seha Thach — Tra Vinh University, 2025"}
  ],
  "sequences": [{
    "@id": f"{BASE}/sequence/normal",
    "@type": "sc:Sequence",
    "label": "Current Pages",
    "canvases": []
  }]
}

for idx, r in enumerate(rows, start=1):
    kpl = r["kpl_id"]
    w, h = int(r["width"]), int(r["height"])
    canvas_uri = f"{BASE}/canvas/{kpl}"
    image_uri = f"{BASE}/{kpl}.jpg"
    
    canvas = {
      "@id": canvas_uri,
      "@type": "sc:Canvas",
      "label": f"Page {idx}",
      "width": w,
      "height": h,
      "images": [{
        "@id": f"{BASE}/annotation/{kpl}-image",
        "@type": "oa:Annotation",
        "motivation": "sc:painting",
        "resource": {
          "@id": image_uri,
          "@type": "dctypes:Image",
          "format": "image/jpeg",
          "width": w,
          "height": h
        },
        "on": canvas_uri
      }],
      "otherContent": [{
        "@id": f"{BASE}/annos/{kpl}.json",
        "@type": "sc:AnnotationList"
      }]
    }
    manifest["sequences"][0]["canvases"].append(canvas)

(ROOT / "manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print("manifest.json generated")
