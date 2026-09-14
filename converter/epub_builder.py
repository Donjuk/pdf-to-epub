"""Montagem de EPUB2 compatível com leitores e-ink simples."""

from __future__ import annotations

import html
import re
import uuid
from pathlib import Path

from ebooklib import epub

from .device import DevicePreset, XTEINK_X3
from .extract import Block, Chapter, ExtractedBook


def _slug(text: str, fallback: str = "cap") -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return (text[:40] or fallback)


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def _block_to_html(block: Block, image_name: str | None = None) -> str:
    if block.kind == "heading":
        tag = f"h{min(max(block.level, 1), 3)}"
        return f"<{tag}>{_escape(block.text)}</{tag}>\n"
    if block.kind == "image" and image_name:
        return (
            f'<p class="no-indent"><img src="{image_name}" alt="" /></p>\n'
        )
    if block.kind == "paragraph":
        return f"<p>{_escape(block.text)}</p>\n"
    return ""


def _chapter_html(chapter: Chapter, image_map: dict[int, str]) -> str:
    # ebooklib envelopa o conteúdo; enviar só o body interno
    parts: list[str] = []
    start = 0
    if (
        chapter.blocks
        and chapter.blocks[0].kind == "heading"
        and chapter.blocks[0].text.strip() == chapter.title.strip()
    ):
        parts.append(f"<h1>{_escape(chapter.title)}</h1>\n")
        start = 1
    elif chapter.title and chapter.title not in ("Início", "Conteúdo"):
        parts.append(f"<h1>{_escape(chapter.title)}</h1>\n")

    for idx, block in enumerate(chapter.blocks[start:], start=start):
        img_name = image_map.get(idx)
        parts.append(_block_to_html(block, img_name))

    if not parts:
        parts.append("<p></p>\n")
    return "".join(parts)


def build_epub(
    book: ExtractedBook,
    output_path: Path,
    device: DevicePreset = XTEINK_X3,
) -> Path:
    epub_book = epub.EpubBook()
    book_id = str(uuid.uuid4())
    epub_book.set_identifier(book_id)
    epub_book.set_title(book.title)
    epub_book.set_language("pt")
    epub_book.add_author(book.author)

    # Metadados úteis
    epub_book.add_metadata("DC", "publisher", f"Conversor Xteink ({device.name})")
    epub_book.add_metadata(
        "DC",
        "description",
        f"Convertido para {device.name} ({device.width_px}×{device.height_px}, "
        f'{device.screen_inch}") a partir de PDF.',
    )

    style_item = epub.EpubItem(
        uid="style",
        file_name="style.css",
        media_type="text/css",
        content=device.css.encode("utf-8"),
    )
    epub_book.add_item(style_item)

    spine_items: list = ["nav"]
    toc: list = []
    used_names: set[str] = set()

    for chap_idx, chapter in enumerate(book.chapters):
        base = _slug(chapter.title, fallback=f"cap-{chap_idx + 1}")
        name = base
        n = 2
        while name in used_names:
            name = f"{base}-{n}"
            n += 1
        used_names.add(name)

        image_map: dict[int, str] = {}
        for block_idx, block in enumerate(chapter.blocks):
            if block.kind != "image" or not block.image_bytes:
                continue
            img_file = f"images/{name}-{block_idx}.{block.image_ext}"
            media = "image/jpeg" if block.image_ext in ("jpg", "jpeg") else "image/png"
            img_item = epub.EpubItem(
                uid=f"img-{name}-{block_idx}",
                file_name=img_file,
                media_type=media,
                content=block.image_bytes,
            )
            epub_book.add_item(img_item)
            image_map[block_idx] = img_file

        chapter_file = f"{name}.xhtml"
        c = epub.EpubHtml(title=chapter.title, file_name=chapter_file, lang="pt")
        c.content = _chapter_html(chapter, image_map)
        c.add_item(style_item)
        epub_book.add_item(c)
        spine_items.append(c)
        toc.append(epub.Link(chapter_file, chapter.title, name))

    epub_book.toc = tuple(toc)
    epub_book.add_item(epub.EpubNcx())
    epub_book.add_item(epub.EpubNav())
    epub_book.spine = spine_items

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(output_path), epub_book, {})
    return output_path
