/* Brevia popup — compresor standalone (funciona en cualquier sitio) */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  let last = "";

  function fmt(n) { return n.toLocaleString("es"); }

  $("go").addEventListener("click", () => {
    const text = $("in").value;
    if (!text.trim()) return;
    const r = globalThis.Brevia.compress(text, { aggressive: $("aggr").checked });
    last = r.text;
    $("in").value = r.text;
    $("pct").textContent = "−" + r.pct + "% tokens";
    $("tok").textContent = fmt(r.tokensIn) + " → " + fmt(r.tokensOut) + "  (−" + fmt(r.saved) + ")";
    $("byt").textContent = fmt(r.bytesIn) + " → " + fmt(r.bytesOut) + "  (−" + fmt(r.bytesSaved) + " B)";
    $("stats").style.display = "block";
  });

  $("copy").addEventListener("click", async () => {
    const txt = last || $("in").value;
    if (!txt) return;
    try {
      await navigator.clipboard.writeText(txt);
      $("copy").textContent = "¡Copiado!";
      setTimeout(() => ($("copy").textContent = "Copiar"), 1200);
    } catch (e) {
      $("in").select();
      document.execCommand("copy");
      $("copy").textContent = "¡Copiado!";
      setTimeout(() => ($("copy").textContent = "Copiar"), 1200);
    }
  });
})();
