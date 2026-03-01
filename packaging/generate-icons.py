#!/usr/bin/env python3
"""
Generate PNG icon set for plex-file-renamer at all standard hicolor sizes.

Design: dark rounded square, horizontal film strip in Plex orange,
white play triangle, and a small pencil in the bottom-right to indicate renaming.
"""

import math
import os
from PIL import Image, ImageDraw

# ── Colours ────────────────────────────────────────────────────────────────────
BG        = (22,  22,  42,  255)   # #16162a  dark navy
ORANGE    = (229, 160,  13,  255)  # #E5A00D  Plex orange
ORANGE_DK = (180, 120,   8,  255)  # darker orange for sprocket strips
FRAME_BG  = ( 12,  12,  28,  255)  # #0c0c1c  very dark (center frame)
WHITE     = (255, 255, 255,  255)
PENCIL_YL = (255, 210,  60,  255)  # pencil body
PENCIL_WD = (220, 185, 110,  255)  # pencil wood tip
GRAPHITE  = ( 60,  60,  60,  255)
ERASER    = (230, 100, 100,  255)
METAL     = (180, 180, 180,  255)
TRANSP    = (  0,   0,   0,    0)


def s(val, size):
    """Scale a 512-baseline value to the target size."""
    return int(round(val * size / 512))


def draw_rounded_rect(draw, xy, radius, fill):
    """Draw a filled rounded rectangle (works on Pillow < 8.2 too)."""
    x0, y0, x1, y1 = xy
    r = radius
    draw.rectangle([x0 + r, y0, x1 - r, y1], fill=fill)
    draw.rectangle([x0, y0 + r, x1, y1 - r], fill=fill)
    draw.ellipse([x0, y0, x0 + 2*r, y0 + 2*r], fill=fill)
    draw.ellipse([x1 - 2*r, y0, x1, y0 + 2*r], fill=fill)
    draw.ellipse([x0, y1 - 2*r, x0 + 2*r, y1], fill=fill)
    draw.ellipse([x1 - 2*r, y1 - 2*r, x1, y1], fill=fill)


def make_pencil_image(size):
    """
    Draw a horizontal pencil pointing RIGHT on a transparent image,
    then rotate it 45° counter-clockwise so it points upper-right.
    We'll paste it so the TIP lands in the lower-right of the icon.

    Returns (pencil_img, paste_offset) where paste_offset is (x, y).
    """
    W = s(220, size)
    H = s(60,  size)
    if W < 4 or H < 4:
        return None, None

    img = Image.new('RGBA', (W, H), TRANSP)
    d   = ImageDraw.Draw(img)

    # proportions
    ex0  = s(  0, size); ex1  = s( 28, size)  # eraser
    mb0  = s( 28, size); mb1  = s( 44, size)  # metal band
    by0  = s( 44, size); by1  = s(156, size)  # body
    tip0 = s(156, size); tipW = s(220, size)  # wood tip
    gtip = s(192, size)                        # graphite start
    ytop = s(  4, size); ybot = s( 56, size)  # vertical extent
    ymid = H // 2

    # eraser
    draw_rounded_rect(d, [ex0, ytop+s(2,size), ex1, ybot-s(2,size)],
                      max(1, s(4,size)), ERASER)
    # metal band
    d.rectangle([mb0, ytop, mb1, ybot], fill=METAL)
    # body
    d.rectangle([by0, ytop, by1, ybot], fill=PENCIL_YL)
    # wood tip (trapezoid)
    d.polygon([
        (tip0, ytop), (tip0, ybot),
        (tipW, ymid)
    ], fill=PENCIL_WD)
    # graphite
    d.polygon([
        (gtip, ytop + s(16,size)), (gtip, ybot - s(16,size)),
        (tipW, ymid)
    ], fill=GRAPHITE)

    # Rotate 225° counter-clockwise ≡ 135° clockwise → tip points lower-right
    rotated = img.rotate(225, expand=True)
    return rotated


def create_icon(size):
    img  = Image.new('RGBA', (size, size), TRANSP)
    draw = ImageDraw.Draw(img)

    # ── background ─────────────────────────────────────────────────────────────
    bg_r = max(4, s(88, size))
    draw_rounded_rect(draw, [0, 0, size - 1, size - 1], bg_r, BG)

    # ── film strip ─────────────────────────────────────────────────────────────
    strip_y1 = s(178, size)
    strip_y2 = s(334, size)
    sp_w     = s( 78, size)   # sprocket strip width

    # left + right orange sprocket strips
    draw.rectangle([0,          strip_y1, sp_w,          strip_y2], fill=ORANGE_DK)
    draw.rectangle([size - sp_w, strip_y1, size - 1,     strip_y2], fill=ORANGE_DK)

    # center frame (dark, inside the strip)
    draw.rectangle([sp_w, strip_y1, size - sp_w, strip_y2], fill=FRAME_BG)

    # thin orange top/bottom rails on the frame edges
    rail_h = max(1, s(6, size))
    draw.rectangle([sp_w, strip_y1,          size - sp_w, strip_y1 + rail_h], fill=ORANGE)
    draw.rectangle([sp_w, strip_y2 - rail_h, size - sp_w, strip_y2],          fill=ORANGE)

    # sprocket holes (3 per side)
    hole_r = max(1, s(18, size))
    cx_l   = sp_w // 2
    cx_r   = size - sp_w // 2
    strip_h = strip_y2 - strip_y1
    for frac in (0.22, 0.50, 0.78):
        cy = strip_y1 + int(strip_h * frac)
        for cx in (cx_l, cx_r):
            draw.ellipse([cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r], fill=BG)

    # ── play triangle ──────────────────────────────────────────────────────────
    frame_cx = size // 2
    frame_cy = (strip_y1 + strip_y2) // 2
    ph = s(68, size)   # half-height of triangle
    pl = s(56, size)   # left offset from center
    pr = s(74, size)   # right offset from center
    draw.polygon([
        (frame_cx - pl, frame_cy - ph),
        (frame_cx - pl, frame_cy + ph),
        (frame_cx + pr, frame_cy),
    ], fill=WHITE)

    # ── pencil (bottom-right) ──────────────────────────────────────────────────
    if size >= 48:
        pencil = make_pencil_image(size)
        if pencil:
            pw, ph_img = pencil.size
            # position: tip lands around (size*0.91, size*0.91)
            px = s(370, size) - pw // 2
            py = s(370, size) - ph_img // 2
            img.paste(pencil, (px, py), pencil)

    return img


def main():
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'icons')
    os.makedirs(out_dir, exist_ok=True)

    # Standard hicolor theme sizes
    sizes = [16, 22, 24, 32, 48, 64, 128, 256, 512]

    for size in sizes:
        icon = create_icon(size)
        path = os.path.join(out_dir, f'plex-file-renamer-{size}.png')
        icon.save(path, 'PNG')
        print(f'  {size:>4}x{size:<4}  →  {path}')

    # Copy 256px as the canonical icon used directly by the .desktop file
    canonical = os.path.join(out_dir, 'plex-file-renamer.png')
    create_icon(256).save(canonical, 'PNG')
    print(f'  canonical  →  {canonical}')
    print('Done.')


if __name__ == '__main__':
    main()
