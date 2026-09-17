"""
matcher.py
Finds the nearest Pantone swatch to a given Lab color, per library,
using CIEDE2000 — the same perceptual color-difference formula used by
professional color-matching/QC software (more accurate than plain
Euclidean Lab distance or CMYK-numeric distance).
"""

import numpy as np
from skimage.color import deltaE_ciede2000


def nearest_match(target_lab, library_entries):
    """
    target_lab: (L, a, b)
    library_entries: list of {"code","name","lab","rgb"}
    Returns the closest entry plus its delta-E, or None if library is empty.
    """
    if not library_entries:
        return None

    t = np.array(target_lab).reshape(1, 1, 3)
    best = None
    best_de = None
    for entry in library_entries:
        e = np.array(entry["lab"]).reshape(1, 1, 3)
        de = deltaE_ciede2000(t, e)[0, 0]
        if best_de is None or de < best_de:
            best_de = de
            best = entry
    result = dict(best)
    result["delta_e"] = round(float(best_de), 2)
    return result


def match_all_libraries(target_lab, libraries):
    """
    libraries: dict[library_name] -> list of entries (from pantone_db)
    Returns dict[library_name] -> match dict (or None)
    """
    return {lib: nearest_match(target_lab, entries) for lib, entries in libraries.items()}


def confidence_note(delta_e):
    """Human-readable read on how good a match is, using standard Delta-E bands."""
    if delta_e is None:
        return "no reference library loaded"
    if delta_e < 1.0:
        return "imperceptible difference"
    if delta_e < 2.0:
        return "very close match"
    if delta_e < 4.0:
        return "close match, minor visible difference"
    if delta_e < 8.0:
        return "noticeable difference"
    return "poor match — no close swatch in library"
