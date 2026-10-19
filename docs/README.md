# SSD project website

Static project page on the `gh-pages` branch. All assets and interactions are
local; no framework, package installation, analytics or build step is required.

## Preview

```bash
git switch gh-pages
python3 -m http.server 8000 --directory docs
```

Open http://localhost:8000. The page shares the visual style of the
[AaltoML LOOK project](https://aaltoml.github.io/look/): warm paper backgrounds,
muted green accents, Cormorant Garamond headings, Inter body text, rounded
content panels, and sticky navigation that highlights the current section.
SSD's content, sample galleries, theory, and experimental comparisons are
maintained here independently. Both fonts are self-hosted with their SIL
Open Font License files in `assets/fonts/`.

## Publish with GitHub Pages

The AaltoML repository publishes automatically from `gh-pages`, `/(root)`.
The `project-page` branch is retained as a migration snapshot. Make website
edits on `gh-pages`, rebuild the root entry page, and push `origin gh-pages`.

GitHub Pages can publish the `gh-pages` branch from either `/(root)` or
`/docs`. Both entry pages render the same academic website. The root entry page
is generated from `docs/index.html` and uses assets under `docs/`.

The project URL is https://aaltoml.github.io/ssd/. The publishing-source
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
  and Cormorant Garamond fonts (SIL Open Font License files retained in `assets/fonts/`).

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
