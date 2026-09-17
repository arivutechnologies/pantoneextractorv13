"""
report.py
Renders the stacked-swatch comparison sheet, matching the layout style
in the reference screenshot: one block per source color, each block
showing the matched Pantone swatches stacked above the original,
with the label centered at the bottom-right of each band and the
Pantone/library code + delta-E printed on it.
"""

from PIL import Image, ImageDraw, ImageFont

BAND_H = 130
BAND_GAP = 12
BLOCK_GAP = 26
WIDTH = 720
MARGIN = 0
FONT_SIZE = 30


_FONT_PATH = None
for _path in (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
):
    try:
        ImageFont.truetype(_path, 10)
        _FONT_PATH = _path
        break
    except Exception:
        continue


def _load_font(size):
    if _FONT_PATH:
        return ImageFont.truetype(_FONT_PATH, size)
    return ImageFont.load_default()


def _fit_font(draw, text, max_width, start_size, min_size=14):
    """Shrink font size until the label fits within max_width."""
    size = start_size
    while size > min_size:
        font = _load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font
        size -= 2
    return _load_font(min_size)


def _text_color_for_bg(rgb):
    r, g, b = rgb
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return (20, 20, 20) if luminance > 150 else (255, 255, 255)


def build_report(color_entries, out_path):
    """
    color_entries: list of dicts, each:
        {
          "original_rgb": (r,g,b),
          "bands": [ (label_text, rgb_or_None), ... ]  # top to bottom,
                    original band should be the LAST tuple in the list
        }
    Saves a single tall PNG and a matching PDF at out_path (.png/.pdf will
    both be written, out_path is used as the stem).
    """
    font = _load_font(FONT_SIZE)
    n_bands_total = sum(len(c["bands"]) for c in color_entries)
    n_gaps_between_bands = sum(len(c["bands"]) - 1 for c in color_entries)
    n_block_gaps = max(0, len(color_entries) - 1)

    height = (
        n_bands_total * BAND_H
        + n_gaps_between_bands * BAND_GAP
        + n_block_gaps * BLOCK_GAP
        + 20
    )

    img = Image.new("RGB", (WIDTH, height), (90, 90, 90))
    draw = ImageDraw.Draw(img)

    side_padding = 24
    max_text_width = WIDTH - 2 * side_padding

    y = 10
    for block in color_entries:
        for i, (label, rgb) in enumerate(block["bands"]):
            fill = rgb if rgb is not None else (60, 60, 60)
            fill_int = tuple(int(round(v)) for v in fill)
            draw.rectangle([MARGIN, y, WIDTH - MARGIN, y + BAND_H], fill=fill_int)

            text_color = _text_color_for_bg(fill_int)
            fitted_font = _fit_font(draw, label, max_text_width, FONT_SIZE)
            bbox = draw.textbbox((0, 0), label, font=fitted_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = max(side_padding, WIDTH - side_padding - tw)
            ty = y + BAND_H - th - 22
            draw.text((tx, ty), label, fill=text_color, font=fitted_font)

            y += BAND_H
            if i < len(block["bands"]) - 1:
                y += BAND_GAP
        y += BLOCK_GAP

    img.save(out_path + ".png")

    # Save the PDF via a palette-mode copy rather than the default RGB path.
    # Pillow's PDF writer normally JPEG-compresses RGB images internally;
    # some Pillow installs (notably certain Windows pip installs) ship
    # without a working JPEG codec, which makes that raise KeyError('JPEG').
    # Converting to palette mode first uses Pillow's Flate-based PDF path
    # instead, which has no JPEG dependency — our swatches are large flat
    # color blocks with text, so 256 colors is plenty and looks identical.
    pdf_img = img.convert("P", palette=Image.ADAPTIVE, colors=256)
    pdf_img.save(out_path + ".pdf")

    return out_path + ".png", out_path + ".pdf"
