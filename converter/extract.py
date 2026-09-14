"""Extração de texto e imagens de PDF."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
from PIL import Image


@dataclass
class Block:
    kind: str  # "heading" | "paragraph" | "image"
    text: str = ""
    level: int = 0
    image_bytes: bytes | None = None
    image_ext: str = "jpg"


@dataclass
class Chapter:
    title: str
    blocks: list[Block] = field(default_factory=list)


@dataclass
class ExtractedBook:
    title: str
    author: str
    chapters: list[Chapter]
    page_count: int


_HEADING_RE = re.compile(
    r"^(?:"
    r"capítulo\s+\d+|capitulo\s+\d+|chapter\s+\d+|"
    r"parte\s+\d+|part\s+\d+|"
    r"seção\s+\d+|secao\s+\d+|section\s+\d+|"
    r"\d+[\.\)]\s+\S|"
    r"[IVXLCDM]+\.\s+\S"
    r")",
    re.IGNORECASE,
)


def _clean_text(text: str) -> str:
    text = text.replace("\u00ad", "")  # soft hyphen
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _looks_like_heading(line: str, avg_size: float, size: float) -> bool:
    line = line.strip()
    if not line or len(line) > 120:
        return False
    if size >= avg_size * 1.18:
        return True
    if _HEADING_RE.match(line) and len(line) < 90:
        return True
    # Linha curta em MAIÚSCULAS (títulos comuns em PDF)
    letters = [c for c in line if c.isalpha()]
    if letters and len(line) < 70:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio > 0.85 and len(letters) >= 4:
            return True
    return False


def _merge_paragraphs(lines: list[str]) -> list[str]:
    """Junta linhas quebradas por layout de página em parágrafos."""
    if not lines:
        return []

    paragraphs: list[str] = []
    buf = lines[0]

    for line in lines[1:]:
        prev = buf.rstrip()
        # Nova linha em branco ⇒ parágrafo novo
        if not line.strip():
            if prev:
                paragraphs.append(prev)
            buf = ""
            continue
        if not prev:
            buf = line.strip()
            continue

        # Hífen de fim de linha
        if prev.endswith("-") and line[:1].islower():
            buf = prev[:-1] + line.lstrip()
            continue

        # Continuidade de frase
        if (
            not prev.endswith((".", "!", "?", ":", ";", '"', "”", "»"))
            and line[:1].islower()
        ):
            buf = prev + " " + line.lstrip()
            continue

        paragraphs.append(prev)
        buf = line.strip()

    if buf.strip():
        paragraphs.append(buf.strip())
    return paragraphs


def _resize_image(raw: bytes, max_width: int) -> tuple[bytes, str]:
    img = Image.open(io.BytesIO(raw))
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize(
            (max_width, max(1, int(img.height * ratio))),
            Image.Resampling.LANCZOS,
        )

    # Escala de cinza ajuda em e-ink
    img = img.convert("L").convert("RGB")

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=72, optimize=True)
    return out.getvalue(), "jpg"


def extract_pdf(
    pdf_path: Path,
    *,
    max_image_width: int = 480,
    include_images: bool = True,
    title_override: str | None = None,
    author_override: str | None = None,
) -> ExtractedBook:
    doc = pymupdf.open(pdf_path)
    meta = doc.metadata or {}
    title = (title_override or meta.get("title") or pdf_path.stem or "Sem título").strip()
    author = (author_override or meta.get("author") or "Desconhecido").strip()

    # Coleta tamanhos de fonte para estimar média
    sizes: list[float] = []
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span.get("text", "").strip():
                        sizes.append(float(span.get("size", 11)))
    avg_size = sum(sizes) / len(sizes) if sizes else 11.0

    chapters: list[Chapter] = []
    current = Chapter(title="Início")
    pending_lines: list[tuple[str, float]] = []

    def flush_text() -> None:
        nonlocal pending_lines, current
        if not pending_lines:
            return
        # Agrupa por heading vs corpo
        body_lines: list[str] = []
        for text, size in pending_lines:
            if _looks_like_heading(text, avg_size, size):
                if body_lines:
                    for para in _merge_paragraphs(body_lines):
                        current.blocks.append(Block(kind="paragraph", text=para))
                    body_lines = []
                # Novo capítulo se o heading for "forte"
                level = 1 if size >= avg_size * 1.25 else 2
                if level == 1 and (current.blocks or chapters):
                    chapters.append(current)
                    current = Chapter(title=text.strip()[:80])
                current.blocks.append(
                    Block(kind="heading", text=text.strip(), level=level)
                )
            else:
                body_lines.append(text)
        if body_lines:
            for para in _merge_paragraphs(body_lines):
                if para:
                    current.blocks.append(Block(kind="paragraph", text=para))
        pending_lines = []

    for page_index, page in enumerate(doc):
        blocks = page.get_text("dict").get("blocks", [])
        # Ordena por posição vertical
        blocks = sorted(blocks, key=lambda b: (b.get("bbox", [0, 0])[1], b.get("bbox", [0])[0]))

        for block in blocks:
            if block.get("type") == 0:  # texto
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue
                    line_text = "".join(s.get("text", "") for s in spans)
                    line_text = _clean_text(line_text)
                    if not line_text:
                        continue
                    max_span_size = max(float(s.get("size", avg_size)) for s in spans)
                    pending_lines.append((line_text, max_span_size))
            elif block.get("type") == 1 and include_images:  # imagem
                flush_text()
                try:
                    xref = block.get("image") or block.get("xref")
                    # Em pymupdf, imagens em blocks dict usam "image" bytes às vezes
                    raw = block.get("image")
                    if isinstance(raw, (bytes, bytearray)):
                        img_bytes, ext = _resize_image(bytes(raw), max_image_width)
                        current.blocks.append(
                            Block(kind="image", image_bytes=img_bytes, image_ext=ext)
                        )
                    elif isinstance(xref, int):
                        pix = pymupdf.Pixmap(doc, xref)
                        if pix.n - pix.alpha > 3:  # CMYK etc
                            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                        raw = pix.tobytes("png")
                        img_bytes, ext = _resize_image(raw, max_image_width)
                        current.blocks.append(
                            Block(kind="image", image_bytes=img_bytes, image_ext=ext)
                        )
                except Exception:
                    # Ignora imagens problemáticas
                    pass

        # Quebra suave entre páginas (evita colar fim/início)
        if pending_lines and not pending_lines[-1][0].endswith(
            (".", "!", "?", ":", ";", '"', "”", "»", "-")
        ):
            # marca parágrafo potencial
            pending_lines.append(("", avg_size))

    flush_text()
    if current.blocks or not chapters:
        chapters.append(current)

    # Remove capítulos vazios
    chapters = [c for c in chapters if c.blocks]
    if not chapters:
        chapters = [
            Chapter(
                title="Conteúdo",
                blocks=[
                    Block(
                        kind="paragraph",
                        text="Não foi possível extrair texto deste PDF. "
                        "Pode ser um PDF escaneado (imagem). "
                        "Nesse caso, use OCR antes de converter.",
                    )
                ],
            )
        ]

    page_count = doc.page_count
    doc.close()
    return ExtractedBook(
        title=title,
        author=author,
        chapters=chapters,
        page_count=page_count,
    )
