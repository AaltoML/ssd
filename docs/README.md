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

In the repository's **Settings → Pages**, choose **Deploy from a branch**, select
`project-page`, and select `/docs`. Save to publish. This follows the
[GitHub Pages publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

The expected project URL is https://wenshuaizhao.github.io/ssd/ once deployment
succeeds. Creating/pushing this branch does not configure or deploy Pages itself.
All asset URLs are relative, so the `/ssd/` project prefix works without changes.

## Edit

- `index.html`: research content, results, authors and citation.
- `styles.css`: responsive layout and appearance.
- `script.js`: BibTeX copy button.
- `assets/`: original paired CelebA PNGs, vector paper figures, and citation.

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
