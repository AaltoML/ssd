# SSD project website

Static project page on the `project-page` branch. All assets and interactions are
local; no framework, package installation, analytics or build step is required.

## Preview

```bash
git switch project-page
python3 -m http.server 8000 --directory docs
```

Open http://localhost:8000. The academic project-page layout follows
[SPMARL](https://wenshuaizhao.github.io/spmarl/): centered title and authors,
affiliations, NeurIPS 2026 venue, Paper/arXiv/Code links, Abstract, Motivation,
Experiments, and BibTeX. Figures and reported numbers come from the camera-ready
manuscript and rebuttal evidence.

## Publish with GitHub Pages

GitHub Pages can publish the `project-page` branch from either `/(root)` or
`/docs`. Both entry pages render the same academic website. The root entry page
is generated from `docs/index.html` and uses assets under `docs/`.

The project URL is https://wenshuaizhao.github.io/ssd/. The publishing-source
configuration follows the [GitHub Pages instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

After changing the site, regenerate the root entry page before committing:

```bash
python3 scripts/build_website.py
```

## Edit

- `index.html`: research content, results, authors and citation.
- `styles.css`: responsive layout and appearance.
- `script.js`: BibTeX copy button and accessible sample-inspection dialog.
- `assets/`: all 36 main-figure CelebA PNGs, appendix gallery and trajectories,
  10 matched hand pairs, vector paper figures, citation, and locally hosted Inter
  font (SIL Open Font License, retained in `assets/fonts/LICENSE.txt`).

The theory section reproduces the covariance identity and directional-variance
analysis with their assumptions. Native MathML keeps the equations selectable.

The sample images are a deliberate small exception to the code repository's
image exclusion rules. Dataset images and generated sample pools are not added.
The page links to `main` for reproduction code, rather than the website branch.

## Verify

```bash
node --check docs/script.js
python3 scripts/check_website.py
```

The checker validates local assets, links to section IDs, image descriptions,
responsive metadata, and parsed SVGs. It does not replace browser layout testing.
