"""Replace embedded PNG panels in a scientific SVG with lossless vector paths.

Usage: python3 scripts/vectorize_svg_panels.py INPUT.svg OUTPUT.svg
Existing transforms, clipping paths, and panel IDs are retained.
"""
import base64
import io
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from PIL import Image
from vector_pixels import SVG, pixel_paths

ET.register_namespace('', SVG)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
source, destination = map(Path, sys.argv[1:])
root = ET.parse(source).getroot()
panels = [n for n in root.iter() if n.tag == f'{{{SVG}}}image']
for panel in panels:
    href = panel.get('{http://www.w3.org/1999/xlink}href') or panel.get('href')
    assert href.startswith('data:image/png;base64,'), 'Expected an embedded PNG'
    image = Image.open(io.BytesIO(base64.b64decode(href.split(',', 1)[1])))
    new = ET.Element(f'{{{SVG}}}svg', {k: v for k, v in panel.attrib.items() if 'href' not in k})
    new.set('viewBox', f'0 0 {image.width} {image.height}')
    pixel_paths(image, new)
    parent = next(n for n in root.iter() if panel in list(n))
    index = list(parent).index(panel)
    parent.remove(panel)
    parent.insert(index, new)
ET.ElementTree(root).write(destination, encoding='utf-8', xml_declaration=True)
print(f'Converted {len(panels)} panels to vector paths: {destination.stat().st_size:,} bytes.')
