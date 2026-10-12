"use strict";

// The same NeurIPS 2026 reference is included in the code repository.
const citation = "@inproceedings{zhao2026sparsely,\n  title     = {Sparsely Supervised Diffusion},\n  author    = {Zhao, Wenshuai and Li, Zhiyuan and Zhao, Yi and\n               Vali, Mohammad Hassan and Trapp, Martin and\n               Pajarinen, Joni and Kannala, Juho and Solin, Arno},\n  booktitle = {Advances in Neural Information Processing Systems},\n  year      = {2026},\n  eprint    = {2602.02699},\n  archivePrefix = {arXiv},\n  primaryClass  = {cs.LG},\n  url       = {https://openreview.net/forum?id=4HalTYbzQG}\n}\n";
const code = document.getElementById("citation-code");
code.textContent = citation;
const button = document.getElementById("copy-citation");
button.addEventListener("click", async () => {
  const status = document.getElementById("copy-status");
  try {
    if (!navigator.clipboard) throw new Error("Clipboard unavailable");
    await navigator.clipboard.writeText(citation);
    button.textContent = "Copied";
    status.textContent = "BibTeX copied to clipboard.";
    window.setTimeout(() => { button.textContent = "Copy BibTeX"; }, 1800);
  } catch {
    const range = document.createRange();
    range.selectNodeContents(code);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    status.textContent = "BibTeX selected. Use your keyboard copy command.";
  }
});
