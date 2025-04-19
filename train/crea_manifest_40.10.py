import os
import json
import re
import csv
from collections import defaultdict

# === CONFIGURAZIONE ===
IMG_DIR = r"C:\Users\Feder\Downloads\pluteo 40.10.v3i.tensorflow\train"
ANNOTATIONS_FILE = os.path.join(IMG_DIR, "_annotations.csv")
BASE_IMAGE_URL = "http://localhost:8000/train"  # Se usi python -m http.server

OUTPUT_MANIFEST = "manifest.json"
MANUSCRIPT_LABEL = "Pluteo 40.10 - Manoscritto medievale"

# === ESTRAE NUMERO DA canvas_cX PER ORDINARE ===
def extract_canvas_index(filename):
    match = re.search(r"canvas_c(\d+)", filename)
    return int(match.group(1)) if match else -1

# === LEGGI ANNOTAZIONI CSV ===
annotations_by_image = defaultdict(list)
with open(ANNOTATIONS_FILE, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # ⬅️ Salta la riga di intestazione
    for row in reader:
        if len(row) < 8:  # Salta righe che non hanno abbastanza valori
            continue
        filename, width, height, label, xmin, ymin, xmax, ymax = row
        annotations_by_image[filename].append({
            "label": label,
            "bbox": [int(xmin), int(ymin), int(xmax), int(ymax)]
        })

# === ORDINA IMMAGINI ===
image_files = [f for f in os.listdir(IMG_DIR) if f.endswith(".jpg")]
image_files.sort(key=extract_canvas_index)

# === CREA MANIFEST IIIF v3 ===
manifest = {
    "@context": "http://iiif.io/api/presentation/3/context.json",
    "id": "http://localhost:8000/train/manifest_40.10.json",
    "type": "Manifest",
    "label": {"en": [MANUSCRIPT_LABEL]},
    "items": []
}

for idx, img_filename in enumerate(image_files):
    canvas_id = f"http://localhost:8000/train/canvas/{idx}"
    annotation_page_id = f"{canvas_id}/annotation_page"

    canvas = {
        "id": canvas_id,
        "type": "Canvas",
        "height": 640,
        "width": 640,
        "label": {"en": [f"Pagina {idx}"]},
        "items": [
            {
                "id": annotation_page_id,
                "type": "AnnotationPage",
                "items": []
            }
        ],
        "thumbnail": [
            {
                "id": f"{BASE_IMAGE_URL}/{img_filename}",
                "type": "Image",
                "format": "image/jpeg"
            }
        ]
    }

    # Aggiungi immagine come painting annotation
    image_annotation = {
        "id": f"{annotation_page_id}/painting",
        "type": "Annotation",
        "motivation": "painting",
        "body": {
            "id": f"{BASE_IMAGE_URL}/{img_filename}",
            "type": "Image",
            "format": "image/jpeg",
            "height": 640,
            "width": 640
        },
        "target": canvas_id
    }
    canvas["items"][0]["items"].append(image_annotation)

    # Aggiungi bounding boxes
    for i, ann in enumerate(annotations_by_image.get(img_filename, [])):
        x1, y1, x2, y2 = ann["bbox"]
        w, h = x2 - x1, y2 - y1
        box_annotation = {
            "id": f"{annotation_page_id}/anno_{i}",
            "type": "Annotation",
            "motivation": "commenting",
            "body": {
                "type": "TextualBody",
                "value": ann["label"],
                "format": "text/plain",
                "language": "en"
            },
            "target": {
                "source": canvas_id,
                "type": "Canvas",
                "selector": {
                    "type": "BoxSelector",
                    "x": x1,
                    "y": y1,
                    "width": w,
                    "height": h
                }
            }
        }
        canvas["items"][0]["items"].append(box_annotation)

    manifest["items"].append(canvas)

# === SALVA MANIFEST ===
with open(os.path.join(IMG_DIR, "manifest_40.10.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print("✅ Manifest creato in: manifest_40.10.json")
