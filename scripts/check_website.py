"""Validate the static project page without framework or browser dependencies."""
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'docs'

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=set();self.references=[];self.fragments=[];self.h1=0
        self.viewport=False;self.language=False
    def handle_starttag(self,tag,attrs):
        data=dict(attrs)
        if 'id' in data:
            if data['id'] in self.ids: raise AssertionError(f'Duplicate ID: {data["id"]}')
            self.ids.add(data['id'])
        if tag=='h1': self.h1+=1
        if tag=='html': self.language=data.get('lang')=='en'
        if tag=='meta' and data.get('name')=='viewport': self.viewport=True
        if tag=='img':
            assert data.get('alt'),f'Missing image description: {data}'
        for attr in ['href','src']:
            value=data.get(attr,'')
            if not value or value=='#' or value.startswith(('https:','http:','data:')): continue
            if value.startswith('#'): self.fragments.append(value[1:])
            else: self.references.append(value.split('#')[0].split('?')[0])

page=Page();page.feed((SITE/'index.html').read_text());page.close()
assert page.language and page.viewport and page.h1==1
for fragment in page.fragments: assert fragment in page.ids,f'Missing section: {fragment}'
for reference in page.references: assert (SITE/reference).is_file(),f'Missing asset: {reference}'
for model in ['baseline','ssd']:
    for sample in [1,6,9]: assert (SITE/'assets'/f'celeba-{model}-{sample}.png').is_file()
for path in (SITE/'assets').glob('*.svg'): ET.parse(path)
for path in SITE.rglob('*'):
    if path.is_file(): assert path.stat().st_size<1_000_000,f'Oversized website file: {path}'
assert (SITE/'.nojekyll').is_file()
print(f'Website check passed: {len(page.ids)} unique IDs, {len(page.references)} local asset references, all sample pairs and SVGs present.')
