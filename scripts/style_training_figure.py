"""Restyle the paper's pdftocairo SVG without changing curve or band geometry.

Usage: python3 scripts/style_training_figure.py INPUT.svg OUTPUT.svg
Create INPUT.svg with: pdftocairo -svg celeba_10k.pdf INPUT.svg
"""
import base64
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

NS = 'http://www.w3.org/2000/svg'
XLINK = 'http://www.w3.org/1999/xlink'
ET.register_namespace('', NS)
ET.register_namespace('xlink', XLINK)
source, destination = map(Path, sys.argv[1:])
root = ET.parse(source).getroot()
# Text runs in the original paper SVG, in document order.
labels = ['1000', '2000', '3000', 'Epoch', '5', '10', 'FID',
          'CelebA 10K', '0', '0.5', '0.95', '0.98']
runs = [n for n in root if any(c.tag == f'{{{NS}}}use' for c in n)]
assert len(runs) == len(labels), 'Unexpected source plot labels'
for run, label in zip(runs, labels):
    first = run[0]
    attrs = {'x': first.get('x'), 'y': first.get('y'),
             'fill': '#384355', 'font-size': '22'}
    if label == 'FID':
        attrs.update(x='26.056222', y='143.5',
                     transform='rotate(-90 26.056222 143.5)', **{'text-anchor': 'middle'})
    elif label == 'CelebA 10K':
        attrs.update(x='289.6', **{'text-anchor': 'middle', 'font-weight': '600'})
    elif label in ['0', '0.5', '0.95', '0.98']:
        attrs['font-size'] = '16'
    text = ET.Element(f'{{{NS}}}text', attrs)
    text.text = label
    index = list(root).index(run)
    root.remove(run)
    root.insert(index, text)
# The only standalone unstroked black path is the outlined eta legend title.
eta_paths = [n for n in root if n.tag == f'{{{NS}}}path'
             and n.get('fill') == 'rgb(0%, 0%, 0%)' and not n.get('stroke')]
assert len(eta_paths) == 1
root.remove(eta_paths[0])
eta = ET.SubElement(root, f'{{{NS}}}text',
                    {'x': '189', 'y': '58', 'font-size': '17', 'fill': '#384355'})
eta.text = 'η'
palette = {
    'rgb(0%, 0%, 0%)': '#233248',
    'rgb(83.920288%, 15.293884%, 15.686035%)': '#2865bb',
    'rgb(17.254639%, 62.744141%, 17.254639%)': '#14877e',
    'rgb(100%, 49.803162%, 5.490112%)': '#8662bc',
    'rgb(69.018555%, 69.018555%, 69.018555%)': '#dfe6ef',
    'rgb(79.998779%, 79.998779%, 79.998779%)': '#dfe6ef',
}
for node in root.iter():
    for attr in ['fill', 'stroke']:
        if node.get(attr) in palette:
            node.set(attr, palette[node.get(attr)])
# Embed the site's licensed font so SVG images render consistently on their own.
font_path = Path(__file__).resolve().parents[1] / 'docs/assets/fonts/InterVariable.woff2'
font = base64.b64encode(font_path.read_bytes()).decode()
style = ET.Element(f'{{{NS}}}style')
style.text = ("@font-face{font-family:Inter;src:url(data:font/woff2;base64," + font +
              ") format('woff2');font-weight:100 900;}text{font-family:Inter,sans-serif;}")
root.insert(0, style)
ET.ElementTree(root).write(destination, encoding='utf-8', xml_declaration=True)
