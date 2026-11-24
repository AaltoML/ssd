"""Build the site's brand assets: favicon, touch icon and link-preview card.

The mark is a 3 x 3 sparse supervision mask: three supervised entries (navy)
among six masked ones (tint). It is the same motif as the talk slides.

Outputs (in docs/assets/):
  favicon.svg            tab icon, adapts to dark browser chrome
  apple-touch-icon.png   180 x 180, opaque, for home screens and bookmarks
  og-image.png           1200 x 630 card used by link previews (og:image)

Usage: python3 scripts/build_brand_assets.py
"""
from pathlib import Path
import random
from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parents[1] / 'docs' / 'assets'
FONTS = Path('/usr/share/fonts/opentype/inter')
INK, INK2, HAIR, FILL = '#1d1d1f', '#6e6e73', '#d2d2d7', '#e8e8ed'
NAVY, NAVY_50, NAVY_10 = '#1f4e79', '#8fa7c0', '#e8eef4'
ON = {(2, 0), (0, 1), (1, 2)}          # supervised cells (col, row)


def cells(origin, cell, gap):
    for r in range(3):
        for c in range(3):
            x, y = origin[0] + c * (cell + gap), origin[1] + r * (cell + gap)
            yield x, y, (c, r) in ON


# ---------- favicon.svg: 64-unit grid, transparent, light/dark aware ----------
rects = ''.join(
    f'<rect class="{"on" if on else "off"}" x="{x}" y="{y}" width="18" height="18" rx="2.5"/>'
    for x, y, on in cells((2, 2), 18, 4))
(ASSETS / 'favicon.svg').write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    f'<style>.on{{fill:{NAVY}}}.off{{fill:#c5d0dc}}'
    f'@media (prefers-color-scheme:dark){{.on{{fill:{NAVY_50}}}.off{{fill:#3a3f46}}}}</style>'
    f'{rects}</svg>\n')


def rounded(draw, box, r, fill):
    draw.rounded_rectangle(box, r, fill=fill)


# ---------- apple-touch-icon.png: opaque white tile ----------
S = 4                                    # supersample, then downscale
img = Image.new('RGB', (180 * S, 180 * S), '#ffffff')
d = ImageDraw.Draw(img)
cell, gap = 34 * S, 8 * S
o = (180 * S - (3 * cell + 2 * gap)) // 2
for x, y, on in cells((o, o), cell, gap):
    rounded(d, (x, y, x + cell, y + cell), 5 * S, NAVY if on else NAVY_10)
img.resize((180, 180), Image.LANCZOS).save(ASSETS / 'apple-touch-icon.png', optimize=True)


# ---------- og-image.png: 1200 x 630 link-preview card ----------
def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size * S)


W, H, M = 1200, 630, 80
img = Image.new('RGB', (W * S, H * S), '#ffffff')
d = ImageDraw.Draw(img)

# sparse-mask motif on the right, about one cell in five supervised
cols, rows, cell, gap = 6, 7, 40, 12
gx, gy = W - M - (cols * cell + (cols - 1) * gap), 92
rng = random.Random(11)
for r in range(rows):
    for c in range(cols):
        x, y = (gx + c * (cell + gap)) * S, (gy + r * (cell + gap)) * S
        rounded(d, (x, y, x + cell * S, y + cell * S), 5 * S, NAVY if rng.random() < .2 else '#eef0f3')

d.text((M * S, 92 * S), 'NeurIPS 2026', font=font('Inter-SemiBold.otf', 28), fill=NAVY)
title = font('InterDisplay-SemiBold.otf', 78)
d.text((M * S, 140 * S), 'Sparsely\nSupervised\nDiffusion', font=title, fill=INK, spacing=4 * S)
d.text((M * S, 438 * S), 'Supervise less. Generate consistently.', font=font('Inter-Regular.otf', 30), fill=INK2)
d.line((M * S, 520 * S, (W - M) * S, 520 * S), fill=HAIR, width=2 * S)
small = font('Inter-Regular.otf', 22)
d.text((M * S, 545 * S), 'Aalto University · Imperial College London · KTH · ELLIS Institute Finland · University of Oulu',
       font=small, fill=INK2)
img.resize((W, H), Image.LANCZOS).save(ASSETS / 'og-image.png', optimize=True)
print('Built favicon.svg, apple-touch-icon.png and og-image.png.')
