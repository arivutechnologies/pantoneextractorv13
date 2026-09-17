"""
pdf_colors.py
Extracts the set of distinct colors actually used in a PDF:

1. Vector colors: fill/stroke colors on every drawn path and text span,
   read directly from the PDF's content streams via PyMuPDF. These are
   exact, not sampled/guessed.
2. Raster colors: for embedded images, we cluster pixels with k-means
   to pull out dominant colors (skipped by default since raster photos
   usually aren't "brand colors" you'd Pantone-match — enable with
   --include-images if you do want it, e.g. logos placed as PNG/JPG).

Returns a de-duplicated list of dicts:
    {"rgb": (r,g,b), "lab": (L,a,b), "source": "vector-fill"/"vector-stroke"/"image",
     "space": "CMYK"/"RGB"/"Gray", "pages": {1,2,...}, "count": n}
"""

from collections import defaultdict
import numpy as np
import pymupdf as fitz  # PyMuPDF (using new import name to avoid deprecation notice)
from sklearn.cluster import KMeans

from color_convert import normalize_pdf_color, rgb_to_lab


def _round_rgb(rgb, precision=0):
    return tuple(round(v, precision) for v in rgb)


def extract_vector_colors(doc):
    """Walk every page's drawing + text objects for fill/stroke colors."""
    found = {}  # key: rounded rgb -> record

    for page_index in range(len(doc)):
        page = doc[page_index]

        # Vector paths (fills & strokes)
        for drawing in page.get_drawings():
            for key, source_label in (("fill", "vector-fill"), ("color", "vector-stroke")):
                col = drawing.get(key)
                if col is None:
                    continue
                n = len(col)
                try:
                    rgb, lab, space = normalize_pdf_color(col, n)
                except ValueError:
                    continue
                rkey = _round_rgb(rgb, 1)
                if rkey not in found:
                    found[rkey] = {
                        "rgb": rgb, "lab": lab, "space": space,
                        "sources": set(), "pages": set(), "count": 0,
                    }
                found[rkey]["sources"].add(source_label)
                found[rkey]["pages"].add(page_index + 1)
                found[rkey]["count"] += 1

        # Text span colors
        text_dict = page.get_text("dict")
        for block in text_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    color_int = span.get("color")
                    if color_int is None:
                        continue
                    # PyMuPDF packs text color as a single sRGB int
                    r = (color_int >> 16) & 255
                    g = (color_int >> 8) & 255
                    b = color_int & 255
                    rgb = (r, g, b)
                    lab = rgb_to_lab(rgb)
                    rkey = _round_rgb(rgb, 1)
                    if rkey not in found:
                        found[rkey] = {
                            "rgb": rgb, "lab": lab, "space": "RGB",
                            "sources": set(), "pages": set(), "count": 0,
                        }
                    found[rkey]["sources"].add("text")
                    found[rkey]["pages"].add(page_index + 1)
                    found[rkey]["count"] += 1

    return found


def extract_image_dominant_colors(doc, k=5, min_area_px=2000):
    """
    Optional: pull dominant colors out of embedded raster images via k-means.
    Only worth doing for things like flattened logos; photos will just add noise.
    """
    found = {}
    for page_index in range(len(doc)):
        page = doc[page_index]
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha >= 4:  # CMYK -> convert to RGB
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                if pix.width * pix.height < min_area_px:
                    continue
                arr = np.frombuffer(pix.samples, dtype=np.uint8)
                channels = pix.n
                arr = arr.reshape(pix.height, pix.width, channels)[:, :, :3]
                pixels = arr.reshape(-1, 3)
                if len(pixels) > 20000:
                    idx = np.random.choice(len(pixels), 20000, replace=False)
                    pixels = pixels[idx]
                kk = min(k, len(np.unique(pixels, axis=0)))
                if kk < 1:
                    continue
                km = KMeans(n_clusters=kk, n_init=4, random_state=0).fit(pixels)
                for center in km.cluster_centers_:
                    rgb = tuple(center)
                    lab = rgb_to_lab(rgb)
                    rkey = _round_rgb(rgb, 1)
                    if rkey not in found:
                        found[rkey] = {
                            "rgb": rgb, "lab": lab, "space": "RGB",
                            "sources": set(), "pages": set(), "count": 0,
                        }
                    found[rkey]["sources"].add("image")
                    found[rkey]["pages"].add(page_index + 1)
                    found[rkey]["count"] += 1
            except Exception:
                continue
    return found


def merge_close_duplicates(color_records, lab_threshold=1.5):
    """
    Colors extracted straight from a PDF often contain tiny rounding
    duplicates (e.g. two paths meant to be the same brand red, off by a
    hair). Merge anything within a small Delta E of each other so the
    report doesn't repeat near-identical swatches.
    """
    from skimage.color import deltaE_ciede2000

    items = list(color_records.values())
    merged = []
    used = [False] * len(items)

    for i, item in enumerate(items):
        if used[i]:
            continue
        group = [item]
        used[i] = True
        for j in range(i + 1, len(items)):
            if used[j]:
                continue
            d = deltaE_ciede2000(
                np.array(item["lab"]).reshape(1, 1, 3),
                np.array(items[j]["lab"]).reshape(1, 1, 3),
            )[0, 0]
            if d < lab_threshold:
                group.append(items[j])
                used[j] = True
        # keep the most frequently occurring variant as representative
        rep = max(group, key=lambda x: x["count"])
        rep = dict(rep)
        rep["sources"] = set().union(*[g["sources"] for g in group])
        rep["pages"] = set().union(*[g["pages"] for g in group])
        rep["count"] = sum(g["count"] for g in group)
        merged.append(rep)

    return merged


def extract_all_colors(pdf_path, include_images=False):
    doc = fitz.open(pdf_path)
    colors = extract_vector_colors(doc)
    if include_images:
        img_colors = extract_image_dominant_colors(doc)
        # merge dicts (image colors keyed separately, combine)
        for k, v in img_colors.items():
            if k in colors:
                colors[k]["sources"] |= v["sources"]
                colors[k]["pages"] |= v["pages"]
                colors[k]["count"] += v["count"]
            else:
                colors[k] = v
    doc.close()
    merged = merge_close_duplicates(colors)
    # sort by how often the color appears (most prominent first)
    merged.sort(key=lambda x: -x["count"])
    return merged
