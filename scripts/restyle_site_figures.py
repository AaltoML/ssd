"""Recolour the website's vector figures to the site palette.

Only chrome colours (backgrounds, axes, arrows, labels, curve colours) are
remapped. Curve geometry and the vectorized pixel panels are untouched.
The script is idempotent: run it after build_method_figure.py or
style_training_figure.py regenerate the SVGs.

Usage: python3 scripts/restyle_site_figures.py
"""
from pathlib import Path
import re

ASSETS = Path(__file__).resolve().parents[1] / 'docs' / 'assets'
INK, INK2, GREY, HAIR, FILL, BAND = '#1d1d1f', '#6e6e73', '#86868b', '#d2d2d7', '#e8e8ed', '#f5f5f7'
BLUE, BLUE_50, BLUE_10 = '#1f4e79', '#8fa7c0', '#e8eef4'
# Earlier (Apple-style) accent values, migrated if a figure still carries them.
OLD_ACCENTS = [('#0071e3', BLUE), ('#80b8f1', BLUE_50), ('#e6f0fc', BLUE_10)]


def swap(text, old, new):
    return text.replace(old, new)


# CelebA-10K training curves: eta = 0 grey (baseline), 0.5 light grey,
# 0.95 light blue, 0.98 blue. Axes and the baseline share #2b302b in the
# source, so they are told apart by stroke width (axes are 0.8).
path = ASSETS / 'celeba10k-training.svg'
svg = path.read_text()
svg = re.sub(r'stroke="#2b302b"([^>]*stroke-width="0\.8")', rf'stroke="{GREY}"\1', svg)
svg = re.sub(r'(stroke-width="0\.8"[^>]*)stroke="#2b302b"', rf'\1stroke="{GREY}"', svg)
for old, new in [('#2b302b', INK2), ('#4c6257', '#c7c7cc'), ('#b08c62', BLUE_50),
                 ('#7b748a', BLUE), ('#3c423b', INK2), ('#d9dbce', FILL), ('#eeece4', '#ffffff')] + OLD_ACCENTS:
    svg = swap(svg, old, new)
path.write_text(svg)

# Paper Figure 2 adaptation: neutral chrome, blue supervision arrows and
# a blue "Sparse" badge. Pixel panels use other colours and are not matched.
path = ASSETS / 'method-overview-figure2.svg'
svg = path.read_text()
for old, new in [('fill="#fffdf8"', 'fill="#ffffff"'), ('stroke="#aeb4a8"', f'stroke="{HAIR}"'),
                 ('fill="#eeece4" stroke="#7d887b"', f'fill="{BAND}" stroke="{GREY}"'),
                 ('stroke="#525c52"', f'stroke="{INK2}"'), ('fill="#525c52"', f'fill="{INK2}"'),
                 ('stroke="#a15a47"', f'stroke="{BLUE}"'), ('fill="#a15a47"', f'fill="{BLUE}"'),
                 ('stroke="#d9dbce"', f'stroke="{FILL}"'),
                 ('fill="#f4eadb"', f'fill="{BAND}"'), ('fill:#84633e', f'fill:{INK2}'),
                 ('fill="#e7eee4"', f'fill="{BLUE_10}"'), ('style="fill:#4c6257"', f'style="fill:{BLUE}"'),
                 ('fill:#3c423b', f'fill:{INK}'), ('fill:#4c6257', f'fill:{INK}'), ('fill:#6c7068', f'fill:{INK2}')] + OLD_ACCENTS:
    svg = swap(svg, old, new)
path.write_text(svg)
print('Restyled celeba10k-training.svg and method-overview-figure2.svg.')
