"""
pantone_db.py
Loads a Pantone reference library from a CSV file that YOU provide.

Why a CSV you provide, instead of a built-in database?
Pantone's exact color values are a licensed, copyrighted dataset owned by
Pantone LLC. This tool can't legally ship that data. But you almost
certainly already have licensed access to it through Adobe Illustrator's
built-in Pantone swatch libraries (Solid Coated, Metallic Coated, and the
CMYK-based Pantone+ library) — see ase_to_csv.py to export those straight
out of Illustrator into the CSV format this tool expects.

Expected CSV columns (header row required):
    library, code, name, Lab_L, Lab_a, Lab_b, C, M, Y, K, R, G, B

- `library` must be one of:  "CMYK", "Metallic Coated", "Solid Coated"
  (matches your three requested categories)
- Fill in whichever value set your source library actually gives you —
  Lab_L/Lab_a/Lab_b (preferred, no conversion loss — this is what
  acb_to_csv.py produces from Adobe's own .acb color book files), OR
  R/G/B, OR C/M/Y/K. Leave the unused columns blank. If more than one
  set is filled in, Lab wins, then RGB, then CMYK.
- `code` is the Pantone number, e.g. "186 C", "P 41-16 C", "10228 C"
- `name` is optional (e.g. "Warm Red"), used only for display

See sample_pantone_library.csv for a tiny worked example (with clearly
fake DEMO values — replace with your real exported library before using
this for production color matching). For real data straight from your
own licensed Adobe install, use acb_to_csv.py (reads Adobe's built-in
.acb Color Book files) or ase_to_csv.py (reads an .ase export from
Illustrator's Swatches panel).
"""

import csv
from collections import defaultdict

from color_convert import cmyk_to_lab, rgb_to_lab

VALID_LIBRARIES = {"CMYK", "Metallic Coated", "Solid Coated"}


def load_pantone_library(csv_path):
    """
    Returns: dict[library_name] -> list of {"code","name","lab","rgb"}
    """
    libraries = defaultdict(list)

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"library", "code"}
        if not required.issubset(set(h.strip() for h in reader.fieldnames or [])):
            raise ValueError(
                f"CSV must have at least columns {required}, "
                f"found: {reader.fieldnames}"
            )

        for row_num, row in enumerate(reader, start=2):
            lib = (row.get("library") or "").strip()
            code = (row.get("code") or "").strip()
            name = (row.get("name") or "").strip()
            if not lib or not code:
                continue
            if lib not in VALID_LIBRARIES:
                raise ValueError(
                    f"Row {row_num}: library '{lib}' not one of {VALID_LIBRARIES}"
                )

            def f_or_none(key):
                v = (row.get(key) or "").strip()
                return float(v) if v not in ("", None) else None

            L, A, Bl = f_or_none("Lab_L"), f_or_none("Lab_a"), f_or_none("Lab_b")
            c, m, y, k = f_or_none("C"), f_or_none("M"), f_or_none("Y"), f_or_none("K")
            r, g, b = f_or_none("R"), f_or_none("G"), f_or_none("B")

            if None not in (L, A, Bl):
                lab = (L, A, Bl)
                from color_convert import lab_to_rgb
                rgb = lab_to_rgb(lab)
            elif None not in (r, g, b):
                lab = rgb_to_lab((r, g, b))
                rgb = (r, g, b)
            elif None not in (c, m, y, k):
                # CMYK values in the CSV are expected as 0-100
                lab = cmyk_to_lab(c / 100, m / 100, y / 100, k / 100)
                from color_convert import cmyk_to_rgb
                rgb = cmyk_to_rgb(c / 100, m / 100, y / 100, k / 100)
            else:
                raise ValueError(
                    f"Row {row_num} ({lib} {code}): needs Lab_L/Lab_a/Lab_b, "
                    f"or full R,G,B, or full C,M,Y,K values"
                )

            libraries[lib].append({"code": code, "name": name, "lab": lab, "rgb": rgb})

    missing = VALID_LIBRARIES - set(libraries.keys())
    if missing:
        print(f"[warning] no entries loaded for library type(s): {missing}. "
              f"Matches for those categories will be skipped.")

    return libraries
