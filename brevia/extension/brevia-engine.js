/* Brevia · motor de compresion (port JS de compress.py)
 * Puro, sin dependencias. Se expone en globalThis.Brevia.
 * Mismo comportamiento que la CLI: seguro por defecto, agresivo opt-in.
 */
(function () {
  "use strict";

  // --- conteo de tokens (estimacion; el navegador no tiene tiktoken) ---
  function countTokens(text) {
    const chars = text.length;
    const words = (text.match(/\S+/g) || []).length;
    return Math.round((chars / 4 + words / 0.75) / 2);
  }

  // --- pasos SEGUROS (sin perdida de significado) ---
  function normalizeWhitespace(text) {
    text = text.replace(/[ \t]+/g, " ");
    text = text.replace(/[ \t]+\n/g, "\n");
    text = text.replace(/\n{3,}/g, "\n\n");
    return text.trim();
  }

  function dedupBlocks(text) {
    const blocks = text.split(/\n\s*\n/);
    const seen = new Set();
    const out = [];
    for (const b of blocks) {
      const key = b.replace(/\s+/g, " ").trim().toLowerCase();
      if (key.length < 12) { out.push(b); continue; }
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(b);
    }
    return out.join("\n\n");
  }

  function trimLines(text) {
    return text.split("\n").map((l) => l.trim()).join("\n");
  }

  // --- pasos AGRESIVOS (opt-in) — bilingue ES/EN ---
  const FILLER = new RegExp(
    [
      "\\bme gustar[ií]a que (?:por favor )?",
      "\\bquisiera (?:pedirte |saber )?(?:si )?",
      "\\bte agradecer[ií]a (?:mucho )?(?:si )?",
      "\\bsi (?:no es mucha molestia|pudieras|fueras tan amable)\\b,?",
      "\\bpor favor\\b,?",
      "\\bla verdad es que\\b,?",
      "\\bcomo te (?:dec[ií]a|comentaba)\\b,?",
      "\\bla neta\\b,?",
      "\\bmuchas gracias(?: de antemano)?\\b\\.?",
      "\\bgracias de antemano\\b\\.?",
      "\\bI was wondering if you could\\b",
      "\\bcould you (?:please )?",
      "\\bwould you (?:kindly|please )?",
      "\\bI would (?:really )?(?:like|appreciate it) (?:if )?",
      "\\bplease\\b,?",
      "\\bthank you(?: (?:so much|in advance))?\\b\\.?",
      "\\bjust (?:wanted|wondering)\\b",
      "\\bas an AI(?: language model)?\\b,?",
      "\\bif that(?:'s| is) (?:ok|okay|alright)\\b,?",
    ].join("|"),
    "gi"
  );

  function stripFiller(text) {
    // protege bloques de codigo ```...``` y `inline`
    const vault = [];
    let protectedText = text.replace(/```[\s\S]*?```|`[^`]+`/g, (m) => {
      vault.push(m);
      return "\x00" + (vault.length - 1) + "\x00";
    });
    protectedText = protectedText.replace(FILLER, "");
    protectedText = protectedText.replace(/[ \t]{2,}/g, " ");
    protectedText = protectedText.replace(/\s+([,.;:!?])/g, "$1");
    return protectedText.replace(/\x00(\d+)\x00/g, (_, i) => vault[parseInt(i, 10)]);
  }

  function collapseMarkdownNoise(text) {
    text = text.replace(/\n-{3,}\n/g, "\n");
    return text;
  }

  const SAFE = [
    ["dedup_parrafos", dedupBlocks],
    ["normalizar_espacios", normalizeWhitespace],
    ["recortar_lineas", trimLines],
  ];
  const AGGRESSIVE = [
    ["quitar_relleno", stripFiller],
    ["reducir_decoracion", collapseMarkdownNoise],
  ];

  const CODE_VAULT = /```[\s\S]*?```|`[^`]+`/g;
  function vaultCode(text) {
    const vault = [];
    const out = text.replace(CODE_VAULT, (m) => {
      vault.push(m);
      return "\x00\x00CODE" + (vault.length - 1) + "\x00\x00";
    });
    return { text: out, vault };
  }
  function restoreCode(text, vault) {
    return text.replace(/\x00\x00CODE(\d+)\x00\x00/g, (_, i) => vault[parseInt(i, 10)]);
  }

  function compress(text, opts) {
    opts = opts || {};
    const steps = opts.aggressive ? SAFE.concat(AGGRESSIVE) : SAFE.slice();
    const before = countTokens(text);
    // blindar el codigo antes de cualquier paso (protege indentacion)
    const vaulted = vaultCode(text);
    let current = vaulted.text;
    const trace = [];
    for (const [name, fn] of steps) {
      const b = countTokens(current);
      current = fn(current);
      const a = countTokens(current);
      trace.push({ paso: name, ahorro: b - a });
    }
    current = normalizeWhitespace(trimLines(normalizeWhitespace(current)));
    current = restoreCode(current, vaulted.vault);
    const after = countTokens(current);
    const bytesIn = new TextEncoder().encode(text).length;
    const bytesOut = new TextEncoder().encode(current).length;
    return {
      text: current,
      tokensIn: before,
      tokensOut: after,
      saved: before - after,
      pct: before ? Math.round(((before - after) / before) * 1000) / 10 : 0,
      bytesIn,
      bytesOut,
      bytesSaved: bytesIn - bytesOut,
      trace,
    };
  }

  globalThis.Brevia = { compress, countTokens };
})();
