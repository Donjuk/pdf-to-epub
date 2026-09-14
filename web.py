"""Local web UI: PDF → EPUB for Xteink X3 (EN / PT / ES)."""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from converter import convert_pdf_to_epub
from converter.device import XTEINK_X3
from converter.i18n import DEFAULT_LANG, LANG_LABELS, SUPPORTED, normalize_lang, t

APP_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = APP_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = "xteink-local-converter"
app.config["MAX_CONTENT_LENGTH"] = 80 * 1024 * 1024  # 80 MB

PAGE = """
<!doctype html>
<html lang="{{ t('html_lang') }}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{ t('page_title') }}</title>
  <style>
    :root {
      --ink: #1a1f1c;
      --paper: #e8ebe4;
      --panel: #f4f6f1;
      --accent: #2f5d50;
      --accent-2: #c45c26;
      --muted: #5c675f;
      --line: #c5cdc4;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", "IBM Plex Sans", system-ui, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(1200px 600px at 10% -10%, #dfe8df 0%, transparent 55%),
        radial-gradient(900px 500px at 100% 0%, #efe4d6 0%, transparent 50%),
        var(--paper);
    }
    main {
      width: min(640px, calc(100% - 2rem));
      margin: 0 auto;
      padding: 3.5rem 0 4rem;
    }
    .top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 1rem;
      margin-bottom: 1.5rem;
      flex-wrap: wrap;
    }
    .device {
      display: inline-flex;
      gap: 0.55rem;
      align-items: baseline;
      font-size: 0.85rem;
      color: var(--accent);
      border-bottom: 1px solid var(--line);
      padding-bottom: 0.35rem;
      margin: 0;
    }
    .lang-switch {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
    }
    .lang-switch > span {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }
    .lang-switch .seg {
      display: inline-flex;
      border: 1px solid var(--line);
      background: #fff;
      overflow: hidden;
    }
    .lang-switch a {
      text-decoration: none;
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 600;
      letter-spacing: 0.02em;
      padding: 0.4rem 0.7rem;
      border-right: 1px solid var(--line);
      min-width: 2.6rem;
      text-align: center;
    }
    .lang-switch a:last-child { border-right: 0; }
    .lang-switch a:hover { color: var(--ink); background: var(--panel); }
    .lang-switch a.active {
      color: #f7faf7;
      background: var(--accent);
    }
    .brand {
      font-size: clamp(1.8rem, 5vw, 2.6rem);
      font-weight: 700;
      letter-spacing: -0.03em;
      margin: 0 0 0.35rem;
      line-height: 1.1;
    }
    .tag {
      color: var(--muted);
      margin: 0 0 2rem;
      font-size: 1.05rem;
      line-height: 1.45;
      max-width: 38ch;
    }
    form {
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 1.35rem 1.25rem 1.4rem;
    }
    label {
      display: block;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      margin: 0.9rem 0 0.35rem;
    }
    label:first-of-type { margin-top: 0; }
    input[type="text"], input[type="file"] {
      width: 100%;
      font: inherit;
      padding: 0.65rem 0.7rem;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
    }
    input[type="file"] {
      padding: 0.55rem;
      background: #fafbf8;
    }
    .row {
      display: flex;
      gap: 0.75rem;
      align-items: center;
      margin-top: 1rem;
      flex-wrap: wrap;
    }
    .check {
      display: flex;
      gap: 0.45rem;
      align-items: center;
      font-size: 0.95rem;
      color: var(--ink);
      text-transform: none;
      letter-spacing: 0;
      margin: 0;
    }
    button {
      margin-top: 1.25rem;
      border: 0;
      background: var(--accent);
      color: #f7faf7;
      font: inherit;
      font-weight: 600;
      padding: 0.75rem 1.2rem;
      cursor: pointer;
    }
    button:hover { filter: brightness(1.05); }
    .flash {
      margin: 0 0 1rem;
      padding: 0.75rem 0.9rem;
      background: #fff7ef;
      border-left: 3px solid var(--accent-2);
      color: var(--ink);
    }
    .hint {
      margin-top: 1.5rem;
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.5;
    }
    .hint code {
      font-family: ui-monospace, Consolas, monospace;
      font-size: 0.88em;
      background: #eef1ea;
      padding: 0.1em 0.35em;
    }
  </style>
</head>
<body>
  <main>
    <div class="top">
      <p class="device">{{ device.name }} · {{ device.width_px }}×{{ device.height_px }} · {{ device.screen_inch }}"</p>
      <nav class="lang-switch" aria-label="{{ t('lang_label') }}">
        <span>{{ t('lang_label') }}</span>
        <div class="seg" role="group">
          {% for code, label in languages.items() %}
            <a href="{{ url_for('set_language', lang=code) }}"
               class="{{ 'active' if code == lang else '' }}"
               hreflang="{{ code }}"
               lang="{{ code }}"
               title="{{ label }}"
               aria-current="{{ 'page' if code == lang else 'false' }}">{{ code|upper }}</a>
          {% endfor %}
        </div>
      </nav>
    </div>

    <h1 class="brand">{{ t('brand') }}</h1>
    <p class="tag">{{ t('tagline') }}</p>

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for m in messages %}
          <p class="flash">{{ m }}</p>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <form method="post" enctype="multipart/form-data" action="{{ url_for('upload') }}">
      <label for="pdf">{{ t('pdf_label') }}</label>
      <input id="pdf" name="pdf" type="file" accept=".pdf,application/pdf" required />

      <label for="title">{{ t('title_label') }}</label>
      <input id="title" name="title" type="text" placeholder="{{ t('title_placeholder') }}" />

      <label for="author">{{ t('author_label') }}</label>
      <input id="author" name="author" type="text" placeholder="{{ t('author_placeholder') }}" />

      <div class="row">
        <label class="check" for="no_images">
          <input id="no_images" name="no_images" type="checkbox" value="1" />
          {{ t('no_images') }}
        </label>
      </div>

      <button type="submit">{{ t('submit') }}</button>
    </form>

    <p class="hint">{{ t('hint') | safe }}</p>
  </main>
</body>
</html>
"""


def _current_lang() -> str:
    return normalize_lang(session.get("lang") or DEFAULT_LANG)


def _detect_browser_lang() -> str:
    best = request.accept_languages.best_match(list(SUPPORTED))
    return normalize_lang(best)


@app.before_request
def ensure_lang() -> None:
    if "lang" not in session:
        session["lang"] = _detect_browser_lang()


@app.get("/lang/<lang>")
def set_language(lang: str):
    session["lang"] = normalize_lang(lang)
    return redirect(request.referrer or url_for("index"))


@app.get("/")
def index():
    lang = _current_lang()
    return render_template_string(
        PAGE,
        device=XTEINK_X3,
        lang=lang,
        languages=LANG_LABELS,
        t=lambda key: t(lang, key),
    )


@app.post("/upload")
def upload():
    lang = _current_lang()
    file = request.files.get("pdf")
    if not file or not file.filename:
        flash(t(lang, "err_select_pdf"))
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".pdf"):
        flash(t(lang, "err_pdf_ext"))
        return redirect(url_for("index"))

    title = (request.form.get("title") or "").strip() or None
    author = (request.form.get("author") or "").strip() or None
    include_images = request.form.get("no_images") != "1"

    job_id = uuid.uuid4().hex[:10]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        pdf_path = tmp_path / filename
        file.save(pdf_path)

        out_name = Path(filename).with_suffix(".epub").name
        out_path = OUTPUT_DIR / f"{job_id}_{out_name}"

        try:
            convert_pdf_to_epub(
                pdf_path,
                out_path,
                device="x3",
                include_images=include_images,
                title=title,
                author=author,
            )
        except Exception as exc:  # noqa: BLE001 — UI feedback
            flash(t(lang, "err_convert", error=exc))
            return redirect(url_for("index"))

    return send_file(
        out_path,
        as_attachment=True,
        download_name=out_name,
        mimetype="application/epub+zip",
    )


def main() -> None:
    print("Open http://127.0.0.1:5000")
    print(f"Generated EPUBs: {OUTPUT_DIR}")
    print("Languages: EN / PT / ES")
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    main()
