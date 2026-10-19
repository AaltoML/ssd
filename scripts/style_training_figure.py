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
# Crop the margin left by the former centered axis labels.
root.attrib.update(viewBox='28 8 485 280', width='485pt', height='280pt')
# Text runs in the original paper SVG, in document order.
labels = ['1000', '2000', '3000', 'Epoch', '5', '10', 'FID',
          'CelebA 10K', '0', '0.5', '0.95', '0.98']
runs = [n for n in root if any(c.tag == f'{{{NS}}}use' for c in n)]
assert len(runs) == len(labels), 'Unexpected source plot labels'
for run, label in zip(runs, labels):
    first = run[0]
    attrs = {'x': first.get('x'), 'y': first.get('y'),
             'fill': '#3c423b', 'font-size': '13'}
    if label == 'FID':
        attrs.update(x='72.4', y='24', **{'text-anchor': 'middle'})
    elif label == 'Epoch':
        attrs.update(x='506.8', y='274', **{'text-anchor': 'end'})
    elif label == 'CelebA 10K':
        attrs.update(x='289.6', **{'text-anchor': 'middle', 'font-weight': '600'})
    elif label in ['0', '0.5', '0.95', '0.98']:
        attrs['font-size'] = '10'
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
                    {'x': '189', 'y': '58', 'font-size': '11', 'fill': '#3c423b'})
eta.text = 'η'
palette = {
    'rgb(100%, 100%, 100%)': '#eeece4',
    'rgb(0%, 0%, 0%)': '#2b302b',
    'rgb(83.920288%, 15.293884%, 15.686035%)': '#4c6257',
    'rgb(17.254639%, 62.744141%, 17.254639%)': '#b08c62',
    'rgb(100%, 49.803162%, 5.490112%)': '#7b748a',
    'rgb(69.018555%, 69.018555%, 69.018555%)': '#d9dbce',
    'rgb(79.998779%, 79.998779%, 79.998779%)': '#d9dbce',
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
