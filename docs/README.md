# SSD project website

Static project page on the `gh-pages` branch. All assets and interactions are
local; no framework, package installation, analytics or build step is required.

## Preview

```bash
git switch gh-pages
python3 -m http.server 8000 --directory docs
```

Open http://localhost:8000. The layout follows the
[SuperMimic project page](https://supermimic.github.io/): a floating pill
navigation, large centred statements, grey bands, a highlights carousel,
a "closer look" viewer, big-number comparisons, a side-by-side table and an
FAQ. SSD uses still images where SuperMimic uses video. Inter is self-hosted
with its SIL Open Font License in `assets/fonts/`; no external requests.

## Publish with GitHub Pages

The AaltoML repository publishes automatically from `gh-pages`, `/(root)`.
Make website edits on `gh-pages`, rebuild the root entry page, and push
`origin gh-pages`.

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
- `script.js`: reveal on scroll, explore menu, highlights carousel, masking-ratio
  viewer, correlation slider, sample dialog, FAQ toggle and BibTeX copy.
- `assets/`: all 36 main-figure CelebA PNGs, appendix gallery and trajectories,
  10 matched hand pairs, vector paper figures, citation, and locally hosted Inter
  (SIL Open Font License retained in `assets/fonts/`).

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

## Vector figures

The opening diagram adapts **Figure 2** of the camera-ready paper,
`figs/overview2.tex`. `assets/method-overview-figure2.svg` uses native SVG text,
U-Net shapes, arrows, badges, and losslessly vectorized paper panels. The
original source-file hashes are recorded inside its SVG metadata.

Rebuild it from the paper sources with Pillow installed:

```bash
python3 scripts/build_method_figure.py --paper-dir /path/to/paper
python3 scripts/restyle_site_figures.py   # recolour to the site palette
python3 scripts/build_brand_assets.py      # favicon, touch icon, og-image link preview
python3 scripts/build_website.py
```

The training plot and spatial-consistency diagram are also SVG, without
embedded bitmap panels. `scripts/vectorize_svg_panels.py` converts embedded
scientific PNG panels into pixel-exact vector rectangles; it does not resample
or change the data. Generated CelebA and hand photographs remain original PNG
images assembled with HTML/CSS, so the samples themselves are not altered.
