"""UI strings: English, Portuguese, Spanish."""

from __future__ import annotations

DEFAULT_LANG = "en"
SUPPORTED = ("en", "pt", "es")

LANG_LABELS = {
    "en": "English",
    "pt": "Português",
    "es": "Español",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "html_lang": "en",
        "page_title": "PDF → EPUB Converter · Xteink X3",
        "brand": "PDF → EPUB Converter",
        "tagline": (
            "Clean reflowable EPUB for the Xteink X3: lean CSS, "
            "resized images, no embedded fonts."
        ),
        "pdf_label": "PDF file",
        "title_label": "Title (optional)",
        "title_placeholder": "Uses PDF metadata if empty",
        "author_label": "Author (optional)",
        "author_placeholder": "Unknown",
        "no_images": "No images (text only)",
        "submit": "Convert to EPUB",
        "hint": (
            "After conversion, copy the <code>.epub</code> to the X3 microSD "
            "or send it via the official app. Scanned PDFs (image-only) need OCR first. "
            "CLI: <code>python cli.py book.pdf</code>"
        ),
        "err_select_pdf": "Please select a PDF file.",
        "err_pdf_ext": "Please upload a file with a .pdf extension.",
        "err_convert": "Conversion failed: {error}",
        "lang_label": "Language",
    },
    "pt": {
        "html_lang": "pt-BR",
        "page_title": "Conversor PDF → EPUB · Xteink X3",
        "brand": "Conversor PDF → EPUB",
        "tagline": (
            "Gera EPUB reflowable limpo para o Xteink X3: CSS enxuto, "
            "imagens encolhidas, sem fontes embutidas."
        ),
        "pdf_label": "Arquivo PDF",
        "title_label": "Título (opcional)",
        "title_placeholder": "Usa metadados do PDF se vazio",
        "author_label": "Autor (opcional)",
        "author_placeholder": "Desconhecido",
        "no_images": "Sem imagens (só texto)",
        "submit": "Converter para EPUB",
        "hint": (
            "Depois da conversão, copie o <code>.epub</code> para o microSD do X3 "
            "ou envie pelo app oficial. PDFs escaneados (só imagem) precisam de OCR antes. "
            "CLI: <code>python cli.py livro.pdf</code>"
        ),
        "err_select_pdf": "Selecione um arquivo PDF.",
        "err_pdf_ext": "Envie um arquivo com extensão .pdf.",
        "err_convert": "Falha na conversão: {error}",
        "lang_label": "Idioma",
    },
    "es": {
        "html_lang": "es",
        "page_title": "Conversor PDF → EPUB · Xteink X3",
        "brand": "Conversor PDF → EPUB",
        "tagline": (
            "EPUB reflowable limpio para el Xteink X3: CSS ligero, "
            "imágenes reducidas, sin fuentes incrustadas."
        ),
        "pdf_label": "Archivo PDF",
        "title_label": "Título (opcional)",
        "title_placeholder": "Usa los metadatos del PDF si está vacío",
        "author_label": "Autor (opcional)",
        "author_placeholder": "Desconocido",
        "no_images": "Sin imágenes (solo texto)",
        "submit": "Convertir a EPUB",
        "hint": (
            "Tras la conversión, copia el <code>.epub</code> a la microSD del X3 "
            "o envíalo con la app oficial. Los PDF escaneados (solo imagen) necesitan OCR antes. "
            "CLI: <code>python cli.py libro.pdf</code>"
        ),
        "err_select_pdf": "Selecciona un archivo PDF.",
        "err_pdf_ext": "Sube un archivo con extensión .pdf.",
        "err_convert": "Error en la conversión: {error}",
        "lang_label": "Idioma",
    },
}


def normalize_lang(code: str | None) -> str:
    if not code:
        return DEFAULT_LANG
    code = code.lower().strip().replace("_", "-")
    short = code.split("-", 1)[0]
    if short in SUPPORTED:
        return short
    return DEFAULT_LANG


def t(lang: str, key: str, **kwargs: object) -> str:
    lang = normalize_lang(lang)
    text = TRANSLATIONS[lang].get(key) or TRANSLATIONS[DEFAULT_LANG].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
