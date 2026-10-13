"use strict";

// The same NeurIPS 2026 reference is included in the code repository.
const citation = "@inproceedings{zhao2026sparsely,\n  title     = {Sparsely Supervised Diffusion},\n  author    = {Zhao, Wenshuai and Li, Zhiyuan and Zhao, Yi and Vali, Mohammad Hassan and Trapp, Martin and Pajarinen, Joni and Kannala, Juho and Solin, Arno},\n  booktitle = {Advances in Neural Information Processing Systems},\n  year      = {2026}\n}\n";
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

// Resolve assets against this script so both /ssd/ and /ssd/docs/ work.
const assetRoot = new URL('.', document.currentScript.src);
const dialog = document.getElementById('sample-dialog');
const dialogImage = document.getElementById('sample-dialog-image');
const dialogTitle = document.getElementById('sample-dialog-title');
document.querySelectorAll('[data-image]').forEach(button => {
  button.addEventListener('click', () => {
    dialogImage.src = new URL(button.dataset.image, assetRoot).href;
    dialogImage.alt = button.dataset.title;
    dialogTitle.textContent = button.dataset.title;
    dialogImage.classList.toggle('marked-error', button.classList.contains('marked-error'));
    dialog.showModal();
  });
});
document.getElementById('close-sample').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  if (event.target === dialog) {
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right ||
        event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
  }
});
