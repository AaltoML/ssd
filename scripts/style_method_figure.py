"""Replace the method diagram's outlined labels with the site's Inter font.

Usage: python3 scripts/style_method_figure.py INPUT.svg OUTPUT.svg
Create INPUT.svg with: pdftocairo -svg overview_1.pdf INPUT.svg
Diagram geometry and image content are preserved.
"""
import base64
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
source, destination = map(Path, sys.argv[1:])
root = ET.parse(source).getroot()
labels = ['Model', 'Supervised Signals', 'U-Net', 'U-Net', 'Masked',
          'Flow Matching', 'SMD', 'Input Noise', 'Clean Image', 'Forward', 'Backward']
runs = [n for n in root.iter()
        if any(c.tag == f'{{{NS}}}use' and 'glyph' in str(c.attrib) for c in n)]
assert len(runs) == len(labels), 'Unexpected source diagram labels'
for run, label in zip(runs, labels):
    parent = next(n for n in root.iter() if run in list(n))
    attrs = {'x': run[0].get('x'), 'y': run[0].get('y'),
             'font-size': '8.2', 'fill': '#384355'}
    if label == 'Flow Matching':
        attrs.update(x='10.19614', y='52.5', transform='rotate(-90 10.19614 52.5)',
                     **{'text-anchor': 'middle'})
    elif label == 'SMD':
        attrs.update(x='10.382299', y='134.4', transform='rotate(-90 10.382299 134.4)',
                     **{'text-anchor': 'middle'})
    text = ET.Element(f'{{{NS}}}text', attrs)
    text.text = label
    index = list(parent).index(run)
    parent.remove(run)
    parent.insert(index, text)
font_path = Path(__file__).resolve().parents[1] / 'docs/assets/fonts/InterVariable.woff2'
font = base64.b64encode(font_path.read_bytes()).decode()
style = ET.Element(f'{{{NS}}}style')
style.text = ("@font-face{font-family:Inter;src:url(data:font/woff2;base64," + font +
              ") format('woff2');font-weight:100 900;}text{font-family:Inter,sans-serif;}")
root.insert(0, style)
ET.ElementTree(root).write(destination, encoding='utf-8', xml_declaration=True)
