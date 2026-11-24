"use strict";
// SSD project page. No dependencies. Works from /ssd/ (root entry page) and /ssd/docs/.
const assetRoot = new URL(".", document.currentScript.src);
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

// ---------- reveal on scroll ----------
(() => {
  const items = $$(".rv");
  if (!("IntersectionObserver" in window) || reduce.matches) { items.forEach(n => n.classList.add("in")); return; }
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
  }), { rootMargin: "0px 0px -8% 0px" });
  items.forEach(n => io.observe(n));
})();

// ---------- explore menu ----------
(() => {
  const btn = $("#exploreBtn"), menu = $("#exploreMenu");
  const set = open => { menu.hidden = !open; btn.setAttribute("aria-expanded", String(open)); };
  btn.addEventListener("click", e => { e.stopPropagation(); set(menu.hidden); });
  menu.addEventListener("click", e => { if (e.target.closest("a")) set(false); });
  document.addEventListener("click", e => { if (!menu.hidden && !e.target.closest(".explore")) set(false); });
  document.addEventListener("keydown", e => { if (e.key === "Escape" && !menu.hidden) { set(false); btn.focus(); } });
})();

// ---------- highlights carousel: dots fill while a card dwells, then advance ----------
(() => {
  const track = $("#hlTrack"), pager = $("#hlPager"), play = $("#hlPlay"), icon = $("#hlPlayIcon");
  const cards = $$(".hcard", track), DWELL = 6000;
  const PAUSE = "M4 2.5h3.4v13H4zM10.6 2.5H14v13h-3.4z", PLAY = "M5 2.5v13l11-6.5z";
  let cur = 0, start = 0, playing = !reduce.matches, visible = false, raf = 0, elapsed = 0;
  const dots = cards.map((_, i) => {
    const d = document.createElement("button");
    d.type = "button"; d.className = "dot"; d.innerHTML = "<i></i>";
    d.setAttribute("aria-label", `Highlight ${i + 1} of ${cards.length}`);
    d.addEventListener("click", () => { go(i); elapsed = 0; start = performance.now(); });
    pager.append(d); return d;
  });
  function mark(i) {
    cur = i;
    dots.forEach((d, j) => { d.classList.toggle("on", j === i); d.toggleAttribute("aria-current", j === i); d.style.removeProperty("--p"); });
    $("i", dots[i]).style.setProperty("--p", playing ? 0 : 1);
  }
  function go(i) {
    const card = cards[i];
    track.scrollTo({ left: card.offsetLeft - parseFloat(getComputedStyle(track).paddingLeft), behavior: reduce.matches ? "auto" : "smooth" });
    mark(i);
  }
  function tick(now) {
    if (playing && visible) {
      const p = Math.min(1, (elapsed + now - start) / DWELL);
      $("i", dots[cur]).style.setProperty("--p", p);
      if (p >= 1) { elapsed = 0; start = now; go((cur + 1) % cards.length); }
    }
    raf = requestAnimationFrame(tick);
  }
  function setPlaying(v) {
    if (!v) elapsed += performance.now() - start; else start = performance.now();
    playing = v; icon.setAttribute("d", v ? PAUSE : PLAY);
    play.setAttribute("aria-label", v ? "Pause highlights" : "Play highlights");
    if (!v) $("i", dots[cur]).style.setProperty("--p", 1);
  }
  play.addEventListener("click", () => setPlaying(!playing));
  // a swipe or scroll by hand selects the nearest card and stops autoplay
  let st;
  track.addEventListener("scroll", () => {
    clearTimeout(st);
    st = setTimeout(() => {
      const x = track.scrollLeft + track.clientWidth / 2;
      const i = cards.reduce((b, c, j) => Math.abs(c.offsetLeft + c.offsetWidth / 2 - x) < Math.abs(cards[b].offsetLeft + cards[b].offsetWidth / 2 - x) ? j : b, 0);
      if (i !== cur) { if (playing) setPlaying(false); mark(i); }
    }, 120);
  }, { passive: true });
  new IntersectionObserver(es => es.forEach(e => {
    const was = visible; visible = e.isIntersecting;
    if (visible && !was) start = performance.now();
    if (!visible && was && playing) elapsed += performance.now() - start;
  }), { threshold: .4 }).observe(track);
  setPlaying(playing); mark(0); raf = requestAnimationFrame(tick);
})();

// ---------- how it works: light the steps in order ----------
(() => {
  const svgs = $$(".lp-svg");
  const light = svg => {
    const steps = [...$$(".lp-nd", svg), ...$$(".lp-bptt, .lp-bl", svg)];
    steps.forEach((n, i) => setTimeout(() => n.classList.add("on"), reduce.matches ? 0 : i < 3 ? i * 450 : 1500));
  };
  if (!("IntersectionObserver" in window)) { svgs.forEach(light); return; }
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { light(e.target); io.unobserve(e.target); }
  }), { threshold: .5 });
  svgs.forEach(s => io.observe(s));
})();

// ---------- closer look: switch the masking ratio for the same nine noises ----------
(() => {
  const chips = $$("#chips .chip"), faces = $("#faces"), read = $("#stageRead"), desc = $("#vwDesc");
  const label = { 0: "η = 0 (baseline)", 2: "η = 0.2", 5: "η = 0.5", 8: "η = 0.8" };
  function select(chip) {
    const eta = chip.dataset.eta;
    chips.forEach(c => { const on = c === chip; c.toggleAttribute("data-open", on); $("button", c).setAttribute("aria-pressed", String(on)); });
    desc.innerHTML = $("p", chip).innerHTML;
    read.textContent = `CelebA-50K · 64 × 64 · ${label[eta]}`;
    faces.classList.add("swap");
    $$("img", faces).forEach((img, i) => {
      img.src = img.src.replace(/celeba-eta-\d-(\d)\.png/, `celeba-eta-${eta}-$1.png`);
      img.alt = `CelebA sample ${i + 1}, ${eta === "0" ? "baseline at eta 0" : `SSD at eta 0.${eta}`}`;
    });
    setTimeout(() => faces.classList.remove("swap"), reduce.matches ? 0 : 160);
  }
  chips.forEach(c => $("button", c).addEventListener("click", () => select(c)));
  desc.innerHTML = $("p", $("#chips .chip[data-open]")).innerHTML;
})();

// ---------- enlarge a sample ----------
(() => {
  const dialog = $("#sample-dialog"), img = $("#sample-dialog-image"), title = $("#sample-dialog-title");
  function open(src, text, err) {
    img.src = src; img.alt = text; title.textContent = text;
    img.classList.toggle("err", !!err);
    dialog.showModal();
  }
  $$("[data-image]").forEach(b => b.addEventListener("click", () =>
    open(new URL(b.dataset.image, assetRoot).href, b.dataset.title, b.classList.contains("err"))));
  $$("#faces .face").forEach(b => b.addEventListener("click", () => { const i = $("img", b); open(i.src, i.alt); }));
  $("#close-sample").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", e => { if (e.target === dialog) dialog.close(); });
})();

// ---------- theory: masked variance p, covariance p², correlation p ----------
(() => {
  const input = $("#corrEta"), out = $("#corrOut");
  const bars = [["#barVar", "#valVar", p => p], ["#barCov", "#valCov", p => p * p], ["#barCor", "#valCor", p => p]];
  function update() {
    const eta = parseFloat(input.value), p = 1 - eta;
    out.textContent = `η = ${eta.toFixed(2)}`;
    bars.forEach(([b, v, f]) => { $(b).style.setProperty("--f", f(p)); $(v).textContent = f(p).toFixed(2); });
  }
  input.addEventListener("input", update); update();
})();

// ---------- carousel arrows ----------
$$(".arrows").forEach(row => {
  const track = document.getElementById(row.dataset.for);
  const [prev, next] = $$(".arrow", row);
  const step = () => (track.firstElementChild.getBoundingClientRect().width + 20);
  const sync = () => { prev.disabled = track.scrollLeft < 4; next.disabled = track.scrollLeft + track.clientWidth > track.scrollWidth - 4; };
  $$(".arrow", row).forEach(a => a.addEventListener("click", () => track.scrollBy({ left: step() * a.dataset.dir, behavior: reduce.matches ? "auto" : "smooth" })));
  track.addEventListener("scroll", sync, { passive: true }); window.addEventListener("resize", sync); sync();
});

// ---------- FAQ expand all ----------
(() => {
  const btn = $("#faqAll"), items = $$("#faqList details");
  const sync = () => {
    const all = items.every(d => d.open);
    btn.setAttribute("aria-expanded", String(all));
    btn.firstChild.textContent = all ? "Collapse all " : "Expand all ";
  };
  btn.addEventListener("click", () => { const open = btn.getAttribute("aria-expanded") !== "true"; items.forEach(d => d.open = open); sync(); });
  items.forEach(d => d.addEventListener("toggle", sync));
})();

// ---------- sticky paper link while the results table is on screen ----------
(() => {
  const cta = $("#stickyCta"), table = $(".ctable");
  if (!("IntersectionObserver" in window)) { cta.classList.add("show"); return; }
  new IntersectionObserver(es => es.forEach(e => cta.classList.toggle("show", e.isIntersecting)), { threshold: .15 }).observe(table);
})();

// ---------- BibTeX ----------
(() => {
  const code = $("#citation-code"), button = $("#copy-citation"), status = $("#copy-status");
  button.addEventListener("click", async () => {
    try {
      if (!navigator.clipboard) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(code.textContent);
      button.textContent = "Copied"; status.textContent = "BibTeX copied to clipboard.";
      setTimeout(() => { button.textContent = "Copy"; }, 1800);
    } catch {
      const range = document.createRange(); range.selectNodeContents(code);
      const sel = getSelection(); sel.removeAllRanges(); sel.addRange(range);
      status.textContent = "BibTeX selected. Use your keyboard copy command.";
    }
  });
})();
