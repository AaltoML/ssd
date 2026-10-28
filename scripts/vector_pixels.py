"""Losslessly express small scientific raster panels as merged SVG rectangles.

This preserves every RGBA pixel. It does not trace, interpolate, or resample.
Runs with the same extent/color on consecutive rows merge into rectangles.
"""
from collections import defaultdict
import xml.etree.ElementTree as ET

SVG = 'http://www.w3.org/2000/svg'

def pixel_paths(image, parent):
    image = image.convert('RGBA')
    active = {}
    rectangles = defaultdict(list)
    pixels = image.load()
    for y in range(image.height + 1):
        current = set()
        if y < image.height:
            x = 0
            while x < image.width:
                color = pixels[x, y]
                end = x + 1
                while end < image.width and pixels[end, y] == color:
                    end += 1
                if color[3]:
                    current.add((x, end - x, color))
                x = end
        for key in set(active) - current:
            start = active.pop(key)
            x, width, color = key
            rectangles[color].append(f'M{x},{start}h{width}v{y-start}h-{width}z')
        for key in current - set(active):
            active[key] = y
    for color, paths in sorted(rectangles.items()):
        r, g, b, alpha = color
        attributes = {'fill': f'#{r:02x}{g:02x}{b:02x}', 'd': ''.join(paths)}
        if alpha < 255:
            attributes['fill-opacity'] = f'{alpha / 255:.8f}'
        ET.SubElement(parent, f'{{{SVG}}}path', attributes)
