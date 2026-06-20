/* Brevia content script — boton flotante que comprime el input del chat in situ.
 * Best-effort: las webs cambian su DOM; si falla el reemplazo inline, el popup
 * siempre funciona como respaldo. Usa execCommand insertText para que React/
 * ProseMirror registren el cambio (set directo de value/textContent no basta).
 */
(function () {
  "use strict";
  if (window.__breviaLoaded) return;
  window.__breviaLoaded = true;

  let aggressive = false;

  // --- encontrar el campo de texto del chat ---
  function findInput() {
    const a = document.activeElement;
    if (a && isEditable(a)) return a;
    // candidatos visibles, el mas grande gana
    const cands = [
      ...document.querySelectorAll('textarea, [contenteditable="true"], div.ProseMirror'),
    ].filter(isVisible);
    cands.sort((x, y) => area(y) - area(x));
    return cands[0] || null;
  }
  function isEditable(el) {
    return (
      el && (el.tagName === "TEXTAREA" || el.isContentEditable || el.getAttribute("contenteditable") === "true")
    );
  }
  function isVisible(el) {
    const r = el.getBoundingClientRect();
    return r.width > 80 && r.height > 18 && r.bottom > 0 && r.top < innerHeight;
  }
  function area(el) { const r = el.getBoundingClientRect(); return r.width * r.height; }

  function readText(el) {
    return el.tagName === "TEXTAREA" ? el.value : el.innerText;
  }

  function writeText(el, text) {
    el.focus();
    if (el.tagName === "TEXTAREA") {
      const setter = Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype, "value"
      ).set;
      setter.call(el, text);
      el.dispatchEvent(new Event("input", { bubbles: true }));
      return true;
    }
    // contenteditable / ProseMirror: seleccionar todo + insertText
    try {
      const sel = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(el);
      sel.removeAllRanges();
      sel.addRange(range);
      const ok = document.execCommand("insertText", false, text);
      if (!ok) { el.innerText = text; el.dispatchEvent(new Event("input", { bubbles: true })); }
      return true;
    } catch (e) {
      el.innerText = text;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      return true;
    }
  }

  function toast(msg, ok) {
    const t = document.createElement("div");
    t.className = "brevia-toast" + (ok ? "" : " err");
    t.textContent = msg;
    document.body.appendChild(t);
    requestAnimationFrame(() => t.classList.add("show"));
    setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 300); }, 2600);
  }

  function run() {
    const el = findInput();
    if (!el) { toast("No encontré el campo de texto. Usa el popup ✦", false); return; }
    const text = readText(el);
    if (!text || !text.trim()) { toast("Escribe algo primero", false); return; }
    const r = globalThis.Brevia.compress(text, { aggressive });
    if (r.saved <= 0) { toast("Ya estaba óptimo — nada que recortar", true); return; }
    writeText(el, r.text);
    toast(`−${r.pct}% tokens · −${r.bytesSaved} B`, true);
  }

  // --- UI flotante ---
  function buildUI() {
    const wrap = document.createElement("div");
    wrap.className = "brevia-wrap";
    wrap.innerHTML = `
      <button class="brevia-btn" title="Comprimir mi prompt con Brevia">✦ Brevia</button>
      <div class="brevia-menu">
        <label class="brevia-row"><input type="checkbox" class="brevia-aggr"> Modo agresivo</label>
        <button class="brevia-go">Comprimir lo que escribí</button>
      </div>`;
    document.body.appendChild(wrap);

    const btn = wrap.querySelector(".brevia-btn");
    const menu = wrap.querySelector(".brevia-menu");
    btn.addEventListener("click", () => wrap.classList.toggle("open"));
    wrap.querySelector(".brevia-aggr").addEventListener("change", (e) => (aggressive = e.target.checked));
    wrap.querySelector(".brevia-go").addEventListener("click", () => { run(); wrap.classList.remove("open"); });
    document.addEventListener("click", (e) => { if (!wrap.contains(e.target)) wrap.classList.remove("open"); });
  }

  if (document.body) buildUI();
  else window.addEventListener("DOMContentLoaded", buildUI);
})();
