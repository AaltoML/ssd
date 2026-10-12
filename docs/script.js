'use strict';

// A fixed illustrative rank order keeps the mask reproducible as eta changes.
const maskGrid = document.getElementById('mask-grid');
const maskRatio = document.getElementById('mask-ratio');
const cells = Array.from({ length: 100 }, (_, index) => {
  const cell = document.createElement('span');
  cell.className = 'mask-cell';
  cell.dataset.rank = String((index * 37 + 11) % 100);
  maskGrid.append(cell);
  return cell;
});
function updateMask() {
  const ratio = Number(maskRatio.value);
  const retained = 100 - ratio;
  cells.forEach(cell => cell.classList.toggle('visible', Number(cell.dataset.rank) < retained));
  document.getElementById('mask-output').textContent = (ratio / 100).toFixed(2);
  document.getElementById('visible-count').textContent = `${retained} / 100`;
  maskRatio.setAttribute('aria-valuetext', `${ratio} percent masked, ${retained} illustrated positions retained`);
}
maskRatio.addEventListener('input', updateMask);
updateMask();

const comparisonSlider = document.getElementById('comparison-slider');
function updateComparison() {
  const percent = Number(comparisonSlider.value);
  document.getElementById('comparison-overlay').style.clipPath = `inset(0 ${100 - percent}% 0 0)`;
  document.getElementById('comparison-line').style.left = `${percent}%`;
  comparisonSlider.setAttribute('aria-valuetext', `${percent} percent SSD, ${100 - percent} percent baseline`);
}
comparisonSlider.addEventListener('input', updateComparison);
updateComparison();

document.querySelectorAll('[data-sample]').forEach(button => {
  button.addEventListener('click', () => {
    const sample = button.dataset.sample;
    document.querySelectorAll('[data-sample]').forEach(item => {
      const selected = item === button;
      item.classList.toggle('selected', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    const baseline = document.getElementById('sample-baseline');
    const ssd = document.getElementById('sample-ssd');
    baseline.src = `assets/celeba-baseline-${sample}.png`;
    baseline.alt = `Baseline CelebA generation, sample ${sample}`;
    ssd.src = `assets/celeba-ssd-${sample}.png`;
    ssd.alt = `SSD CelebA generation at mask ratio 0.8, sample ${sample}`;
  });
});

document.querySelectorAll('[data-copy]').forEach(button => {
  button.addEventListener('click', async () => {
    const code = document.getElementById(button.dataset.copy);
    const status = document.getElementById('copy-status');
    try {
      if (!navigator.clipboard) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(code.textContent);
      const original = button.textContent;
      button.textContent = 'Copied';
      status.textContent = 'Copied to clipboard.';
      window.setTimeout(() => { button.textContent = original; }, 1800);
    } catch {
      const range = document.createRange();
      range.selectNodeContents(code);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = 'Text selected. Use your keyboard copy command.';
    }
  });
});
