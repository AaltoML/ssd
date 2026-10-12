"""Prepare a root entry page for GitHub Pages root-folder publishing.

The academic site is maintained in docs/. This derived entry page keeps the
same project URL working when Pages publishes project-page /(root).
"""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'docs/index.html').read_text()
for prefix in ['href="assets/','src="assets/','href="styles.css"','src="script.js"']:
    target=prefix.replace('="','="docs/',1)
    source=source.replace(prefix,target)
(ROOT/'index.html').write_text(source)
(ROOT/'.nojekyll').touch()
print('Built index.html for Pages root publishing; docs/ remains independently publishable.')
