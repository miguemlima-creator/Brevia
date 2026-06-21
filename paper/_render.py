# -*- coding: utf-8 -*-
"""Convierte PAPER.md en PAPER.html legible (con tablas), para leer en el navegador."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
md_text = (HERE / "PAPER.md").read_text(encoding="utf-8")

try:
    import markdown
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
except Exception:
    # fallback mínimo si no está la librería: <pre> plano
    import html
    body = "<pre style='white-space:pre-wrap'>" + html.escape(md_text) + "</pre>"

html_doc = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Brevia — Paper</title>
<style>
 body{max-width:820px;margin:40px auto;padding:0 20px;background:#fff;color:#1a1a1a;
   font-family:Georgia,'Times New Roman',serif;line-height:1.6;font-size:17px;}
 h1{font-size:30px;line-height:1.2;border-bottom:3px solid #02C39A;padding-bottom:10px;}
 h2{font-size:22px;margin-top:34px;color:#0E1525;border-bottom:1px solid #ddd;padding-bottom:4px;}
 h3{font-size:18px;color:#16203A;}
 code{background:#f4f4f4;padding:1px 5px;border-radius:4px;font-size:14px;}
 pre{background:#0E1525;color:#E8EEF5;padding:14px;border-radius:8px;overflow:auto;font-size:13px;}
 table{border-collapse:collapse;width:100%;margin:16px 0;font-size:15px;}
 th,td{border:1px solid #ccc;padding:8px 10px;text-align:left;}
 th{background:#0F2A20;color:#fff;}
 blockquote{border-left:4px solid #02C39A;margin:16px 0;padding:6px 16px;color:#555;
   background:#f6fdfb;font-style:italic;}
 a{color:#028090;} hr{border:none;border-top:1px solid #ddd;margin:30px 0;}
 strong{color:#0E1525;}
</style></head><body>
""" + body + "</body></html>"

out = HERE / "PAPER.html"
out.write_text(html_doc, encoding="utf-8")
print("HTML generado:", out)
