"""Validate the static project page without framework or browser dependencies."""
from html.parser import HTMLParser
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'docs'

class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=set();self.references=[];self.fragments=[];self.h1=0
        self.viewport=False;self.language=False;self.in_citation=False;self.citation=""
    def handle_starttag(self,tag,attrs):
        data=dict(attrs)
        if 'id' in data:
            if data['id'] in self.ids: raise AssertionError(f'Duplicate ID: {data["id"]}')
            self.ids.add(data['id'])
        if tag=='code' and data.get('id')=='citation-code': self.in_citation=True
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

    def handle_data(self,data):
        if self.in_citation: self.citation+=data
    def handle_endtag(self,tag):
        if tag=='code': self.in_citation=False

page=Page();page.feed((SITE/'index.html').read_text());page.close()
assert page.language and page.viewport and page.h1==1
for fragment in page.fragments: assert fragment in page.ids,f'Missing section: {fragment}'
for reference in page.references: assert (SITE/reference).is_file(),f'Missing asset: {reference}'
for eta in [0,2,5,8]:
    for sample in range(1,10): assert (SITE/'assets'/f'celeba-eta-{eta}-{sample}.png').is_file()
for model in ['baseline','ssd']:
    for sample in range(1,11): assert (SITE/'assets'/f'hands-{model}-{sample}.png').is_file()
assert (SITE/'assets/fonts/InterVariable.woff2').read_bytes()[:4]==b'wOF2'
assert (SITE/'assets/fonts/LICENSE.txt').is_file()
for path in (SITE/'assets').glob('*.svg'): ET.parse(path)
for path in SITE.rglob('*'):
    if path.is_file(): assert path.stat().st_size<3_000_000,f'Oversized website file: {path}'
assert (SITE/'.nojekyll').is_file()
reference=(ROOT/'citation.bib').read_text()
assert (SITE/'assets/citation.bib').read_text()==reference
assert page.citation==reference,'Website BibTeX differs from repository citation'
assert '## Validation and attribution' not in (ROOT/'README.md').read_text()
print(f'Website check passed: {len(page.ids)} unique IDs, {len(page.references)} local asset references, all sample pairs and SVGs present.')

# The branch-root publishing mode must resolve the same website assets.
root_page=Page();root_page.feed((ROOT/'index.html').read_text());root_page.close()
for reference in root_page.references:
    assert (ROOT/reference).is_file(),f'Missing root-page asset: {reference}'
assert root_page.citation==(ROOT/'citation.bib').read_text()
assert (ROOT/'.nojekyll').is_file()
print('Branch-root entry page and asset references passed.')
