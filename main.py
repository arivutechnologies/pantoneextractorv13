"""
main.py — CLI entrypoint.

Usage:
    python main.py input.pdf --library pantone_library.csv --out report

Options:
    --library PATH      CSV of Pantone reference swatches (see pantone_db.py
                         and sample_pantone_library.csv). Required for real
                         matching; without it you'll only get the extracted
                         original colors with no matches.
    --out STEM           Output file stem (writes STEM.png, STEM.pdf, STEM.csv)
    --include-images     Also cluster dominant colors out of embedded raster
                          images (logos etc.), not just vector fills/strokes.
    --max-colors N        Cap how many distinct colors get a full report row
                          (sorted by how often they appear), default 15.
"""

import argparse
import csv
import os
import sys

from pdf_colors import extract_all_colors
from pantone_db import load_pantone_library, VALID_LIBRARIES
from matcher import match_all_libraries, confidence_note
from report import build_report

LIBRARY_ORDER = ["CMYK", "Metallic Coated", "Solid Coated"]
LIBRARY_LABEL = {
    "CMYK": "PANTONE+ CMYK",
    "Metallic Coated": "PANTONE+ METALLIC COATED",
    "Solid Coated": "PANTONE+ SOLID COATED",
}


def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*(int(round(v)) for v in rgb))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf_path")
    ap.add_argument("--library", help="CSV path of Pantone reference swatches")
    ap.add_argument("--out", default="pantone_report")
    ap.add_argument("--include-images", action="store_true")
    ap.add_argument("--max-colors", type=int, default=15)
    args = ap.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"PDF not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting colors from {args.pdf_path} ...")
    colors = extract_all_colors(args.pdf_path, include_images=args.include_images)
    colors = colors[: args.max_colors]
    print(f"Found {len(colors)} distinct color(s).")

    libraries = {}
    if args.library:
        libraries = load_pantone_library(args.library)
    else:
        print("[warning] no --library supplied: report will show extracted colors "
              "only, with no Pantone matches. Pass --library your_pantone.csv.")

    report_blocks = []
    csv_rows = []

    for c in colors:
        matches = match_all_libraries(c["lab"], libraries) if libraries else {}

        bands = []
        for lib_key in LIBRARY_ORDER:
            m = matches.get(lib_key)
            if m:
                label = f"{LIBRARY_LABEL[lib_key]}  {m['code']}"
                bands.append((label, m["rgb"]))
            elif libraries:
                bands.append((f"{LIBRARY_LABEL[lib_key]}  (no library loaded)", None))
        bands.append(("ORIGINAL", c["rgb"]))

        report_blocks.append({"original_rgb": c["rgb"], "bands": bands})

        row = {
            "original_rgb": rgb_to_hex(c["rgb"]),
            "found_on_pages": ";".join(str(p) for p in sorted(c["pages"])),
            "source": ";".join(sorted(c["sources"])),
        }
        for lib_key in LIBRARY_ORDER:
            m = matches.get(lib_key)
            row[f"{lib_key}_code"] = m["code"] if m else ""
            row[f"{lib_key}_delta_e"] = m["delta_e"] if m else ""
            row[f"{lib_key}_confidence"] = confidence_note(m["delta_e"]) if m else ""
        csv_rows.append(row)

    png_path, pdf_path = build_report(report_blocks, args.out)
    print(f"Wrote {png_path}")
    print(f"Wrote {pdf_path}")

    csv_out = args.out + ".csv"
    fieldnames = ["original_rgb", "found_on_pages", "source"] + [
        f"{lib}_{suf}" for lib in LIBRARY_ORDER for suf in ("code", "delta_e", "confidence")
    ]
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Wrote {csv_out}")


if __name__ == "__main__":
    main()
