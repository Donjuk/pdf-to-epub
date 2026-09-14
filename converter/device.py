"""Presets de aparelho para otimização do EPUB."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DevicePreset:
    name: str
    width_px: int
    height_px: int
    ppi: int
    screen_inch: float
    # Largura máxima de imagens embutidas (px)
    max_image_width: int
    # CSS base injetado no EPUB
    css: str


XTEINK_X3 = DevicePreset(
    name="Xteink X3",
    width_px=528,
    height_px=792,
    ppi=259,
    screen_inch=3.7,
    max_image_width=480,
    css="""\
/* Otimizado para Xteink X3 — 3.7" / 528×792 / 259 PPI */
html, body {
  margin: 0;
  padding: 0;
  font-size: 1em;
  line-height: 1.45;
  text-align: justify;
  hyphens: auto;
  -webkit-hyphens: auto;
}
body {
  padding: 0.4em 0.55em;
}
h1, h2, h3, h4, h5, h6 {
  text-align: center;
  text-indent: 0;
  margin: 1.2em 0 0.6em;
  page-break-before: always;
  page-break-after: avoid;
  line-height: 1.25;
}
h1 { font-size: 1.35em; }
h2 { font-size: 1.2em; }
h3 { font-size: 1.1em; }
p {
  margin: 0 0 0.55em;
  text-indent: 1.1em;
  orphans: 2;
  widows: 2;
}
p.no-indent, .no-indent {
  text-indent: 0;
}
blockquote {
  margin: 0.6em 0.8em;
  font-style: italic;
}
img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 0.6em auto;
  page-break-inside: avoid;
}
pre, code {
  font-family: monospace;
  font-size: 0.85em;
  white-space: pre-wrap;
  word-wrap: break-word;
}
a { text-decoration: none; color: inherit; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;
}
td, th {
  border: 1px solid #000;
  padding: 0.2em 0.35em;
  vertical-align: top;
}
""",
)

PRESETS = {
    "x3": XTEINK_X3,
}
