"""
color_convert.py
Color space conversions used throughout the matcher.

We standardize internally on CIE Lab, because perceptual color distance
(Delta E) is only meaningful in a perceptually-uniform space.
"""

import numpy as np
from skimage.color import rgb2lab, lab2rgb


def cmyk_to_rgb(c, m, y, k):
    """
    Naive CMYK -> RGB (0-1 floats in, 0-255 ints out).
    Note: this is a simple device-independent approximation, NOT a proper
    ICC-profile-based conversion. For print-accurate work you'd normally
    convert through your document's actual CMYK ICC profile. For the
    purpose of finding the *nearest* Pantone reference (which itself is
    usually specified as CMYK or Lab in your library file), this
    approximation is standard practice and matches what most simple
    color-matching tools do.
    """
    c, m, y, k = [max(0.0, min(1.0, v)) for v in (c, m, y, k)]
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    return (r, g, b)


def rgb_to_lab(rgb):
    """rgb: tuple/list of 0-255 values -> (L, a, b)"""
    arr = np.array(rgb, dtype=np.float64).reshape(1, 1, 3) / 255.0
    lab = rgb2lab(arr)
    return tuple(lab[0, 0, :])


def cmyk_to_lab(c, m, y, k):
    rgb = cmyk_to_rgb(c, m, y, k)
    return rgb_to_lab(rgb)


def lab_to_rgb(lab):
    arr = np.array(lab, dtype=np.float64).reshape(1, 1, 3)
    rgb = lab2rgb(arr)
    rgb = np.clip(rgb, 0, 1) * 255
    return tuple(rgb[0, 0, :])


def normalize_pdf_color(color_tuple, colorspace_n):
    """
    PyMuPDF returns fill/stroke colors as a tuple whose length tells you
    the colorspace: 1 = Gray, 3 = RGB, 4 = CMYK.
    Returns (rgb_0_255, lab, source_space_str)
    """
    if colorspace_n == 1:
        g = color_tuple[0] * 255
        rgb = (g, g, g)
        space = "Gray"
    elif colorspace_n == 3:
        rgb = tuple(v * 255 for v in color_tuple)
        space = "RGB"
    elif colorspace_n == 4:
        rgb = cmyk_to_rgb(*color_tuple)
        space = "CMYK"
    else:
        raise ValueError(f"Unsupported colorspace with {colorspace_n} components")
    lab = rgb_to_lab(rgb)
    return rgb, lab, space
