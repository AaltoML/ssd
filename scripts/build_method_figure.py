"""Build the website's vector adaptation of paper Figure 2 (overview2.tex).

Usage: python3 scripts/build_method_figure.py --paper-dir /path/to/paper
The three paper panels are losslessly converted to SVG paths. All text,
U-Nets, arrows, badges and stack geometry are native SVG. No bitmaps, external
resources, or plotting approximations are embedded in the published diagram.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import xml.etree.ElementTree as ET
from PIL import Image
from vector_pixels import SVG, pixel_paths

ET.register_namespace('', SVG)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--paper-dir', type=Path, required=True)
args = parser.parse_args()
root_dir = Path(__file__).resolve().parents[1]
figs = args.paper_dir / 'figs'
assert 'overview2.tex' in (args.paper_dir / 'main.tex').read_text()
root = ET.Element(f'{{{SVG}}}svg', {
    'width': '1100', 'height': '570', 'viewBox': '0 0 1100 570',
    'role': 'img', 'aria-labelledby': 'method-title method-description',
})
def add(tag, attributes=None, parent=None, text=None):
    element = ET.SubElement(parent if parent is not None else root,
                            f'{{{SVG}}}{tag}', attributes or {})
    if text is not None:
        element.text = text
    return element
add('title', {'id': 'method-title'}, text='Figure 2: sparsely supervised diffusion')
add('desc', {'id': 'method-description'}, text='Flow matching and SSD use the same full noise input and U-Net. Flow matching supervises the full target velocity. SSD supervises sparse masked target differences, shown as a stack of partial views. Solid arrows indicate the forward pass; dashed arrows indicate supervision.')
source_files = [figs / name for name in ['overview2.tex', 'noise.png', 'velocity.png', 'masked.png']]
add('metadata', text=json.dumps({'source': 'Paper Figure 2, figs/overview2.tex',
    'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
    'conversion': 'Lossless pixel paths; diagram redrawn as native SVG to match website typography.'}))
font = base64.b64encode((root_dir / 'docs/assets/fonts/InterVariable.woff2').read_bytes()).decode()
add('style', text="@font-face{font-family:Inter;src:url(data:font/woff2;base64," + font + ") format('woff2');font-weight:100 900;}text{font-family:Inter,sans-serif;fill:#3c423b}.header{font-size:24px;font-weight:650;fill:#4c6257}.label{font-size:19px}.row{font-size:20px;font-weight:650}.small{font-size:16px;fill:#6c7068}.badge{font-size:17px;font-weight:600}")
defs = add('defs')
for name, color in [('forward', '#525c52'), ('backward', '#a15a47')]:
    marker = add('marker', {'id': name, 'viewBox': '0 0 10 10', 'refX': '9', 'refY': '5', 'markerWidth': '7', 'markerHeight': '7', 'orient': 'auto-start-reverse'}, defs)
    add('path', {'d': 'M0 0L10 5L0 10z', 'fill': color}, marker)
for name in ['noise', 'velocity', 'masked']:
    image = Image.open(figs / (name + '.png'))
    symbol = add('symbol', {'id': 'panel-' + name, 'viewBox': f'0 0 {image.width} {image.height}'}, defs)
    pixel_paths(image, symbol)

def label(value, x, y, cls='label', **attributes):
    return add('text', {'x': str(x), 'y': str(y), 'class': cls, 'text-anchor': 'middle', **attributes}, text=value)
def panel(name, x, y):
    add('rect', {'x':str(x-1), 'y':str(y-1), 'width':'152', 'height':'152', 'fill':'#fffdf8', 'stroke':'#aeb4a8', 'stroke-width':'1.3'})
    add('use', {'href':'#panel-' + name, 'x':str(x), 'y':str(y), 'width':'150', 'height':'150'})
def unet(cy):
    for d in [f'M445 {cy-75}L523 {cy-38}L523 {cy+38}L445 {cy+75}Z',
              f'M625 {cy-75}L547 {cy-38}L547 {cy+38}L625 {cy+75}Z']:
        add('path', {'d':d, 'fill':'#eeece4', 'stroke':'#7d887b', 'stroke-width':'1.5', 'stroke-linejoin':'round'})
    label('U-Net', 535, cy+111, 'small')
def arrow(x1, x2, y, backward=False):
    attrs={'x1':str(x1), 'x2':str(x2), 'y1':str(y), 'y2':str(y), 'stroke':'#a15a47' if backward else '#525c52', 'stroke-width':'2', 'marker-end':'url(#backward)' if backward else 'url(#forward)'}
    if backward:attrs['stroke-dasharray']='7 5'
    add('line', attrs)

for value, cx in [('Input',235),('Model',535),('Supervision',835)]:label(value,cx,40,'header')
add('line', {'x1':'148','x2':'1030','y1':'62','y2':'62','stroke':'#d9dbce'})
for cy, row in [(173,'Flow Matching'),(423,'SSD (Ours)')]:
    label(row,78,cy,'row',transform=f'rotate(-90 78 {cy})')
    panel('noise',160,cy-75)
    label('x₀ (Noise)',235,cy+111)
    unet(cy)
    arrow(323,433,cy)
panel('velocity',760,98)
label('x₁ − x₀',835,284)
arrow(747,637,173,True)
label('fwd',378,157,'small')
label('bwd',692,157,'small')
# The same masked panel is stacked three times, as in the paper's TikZ source.
for dx,dy in [(-30,-24),(-15,-12),(0,0)]:panel('masked',760+dx,348+dy)
label('Masked Diff.',820,534)
for y in [401,423,445]:arrow(717,637,y,True)
for y, value, fill, ink in [(98,'Full-pixel','#f4eadb','#84633e'),(348,'Sparse','#e7eee4','#4c6257')]:
    add('rect', {'x':'953','y':str(y),'width':'47','height':'150','rx':'8','fill':fill})
    label(value,976.5,y+75,'badge',transform=f'rotate(-90 976.5 {y+75})',style=f'fill:{ink}')
path = root_dir / 'docs/assets/method-overview-figure2.svg'
ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
assert path.stat().st_size < 3_000_000
print(f'Built Figure 2 as pure SVG ({path.stat().st_size:,} bytes).')
