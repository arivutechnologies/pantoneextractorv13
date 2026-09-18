"""Vercel Python function: process a PDF and return short-lived browser downloads."""
import base64, csv, io, os, tempfile, uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pdf_colors import extract_all_colors
from pantone_db import load_pantone_library
from matcher import match_all_libraries, confidence_note
from report import build_report

app = FastAPI()
LIBS = ["CMYK", "Metallic Coated", "Solid Coated"]

def _hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*(int(round(v)) for v in rgb))

@app.post("/api/extract")
async def extract(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Please upload a PDF file.")
    raw = await file.read()
    if len(raw) > 4 * 1024 * 1024:
        raise HTTPException(413, "Maximum file size is 4 MB.")
    with tempfile.TemporaryDirectory() as work:
        inp = os.path.join(work, "input.pdf")
        stem = os.path.join(work, "pantone-report")
        with open(inp, "wb") as out: out.write(raw)
        colors = extract_all_colors(inp)[:15]
        library_path = os.path.join(os.path.dirname(__file__), "..", "real_pantone_library.csv")
        libraries = load_pantone_library(library_path)
        blocks, rows = [], []
        for color in colors:
            matches = match_all_libraries(color["lab"], libraries)
            bands = []
            for key in LIBS:
                match = matches.get(key)
                bands.append((f"{key}  {match['code']}" if match else f"{key}  (not loaded)", match["rgb"] if match else None))
            bands.append(("ORIGINAL", color["rgb"]))
            blocks.append({"original_rgb": color["rgb"], "bands": bands})
            row = {"original_rgb": _hex(color["rgb"]), "found_on_pages": ";".join(map(str, sorted(color["pages"]))), "source": ";".join(sorted(color["sources"]))}
            for key in LIBS:
                match = matches.get(key); row[f"{key}_code"] = match["code"] if match else ""; row[f"{key}_delta_e"] = match["delta_e"] if match else ""; row[f"{key}_confidence"] = confidence_note(match["delta_e"]) if match else ""
            rows.append(row)
        png, pdf = build_report(blocks, stem)
        csv_path = stem + ".csv"
        fields = ["original_rgb", "found_on_pages", "source"] + [f"{lib}_{s}" for lib in LIBS for s in ("code", "delta_e", "confidence")]
        with open(csv_path, "w", newline="", encoding="utf-8") as out:
            writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
        files = []
        for label, ext, mime in (("PNG", "png", "image/png"), ("PDF", "pdf", "application/pdf"), ("CSV", "csv", "text/csv")):
            with open(stem + "." + ext, "rb") as out: encoded = base64.b64encode(out.read()).decode()
            files.append({"label": "Download " + label, "ext": ext, "href": f"data:{mime};base64,{encoded}"})
        return JSONResponse({"id": str(uuid.uuid4()), "name": file.filename, "createdAt": 0, "expiresInMinutes": 30, "files": files})
