"""API principal: PDF → EPUB para Xteink."""

from __future__ import annotations

from pathlib import Path

from .device import PRESETS, DevicePreset, XTEINK_X3
from .epub_builder import build_epub
from .extract import extract_pdf


def convert_pdf_to_epub(
    pdf_path: str | Path,
    output_path: str | Path | None = None,
    *,
    device: str | DevicePreset = "x3",
    include_images: bool = True,
    title: str | None = None,
    author: str | None = None,
) -> Path:
    """Converte um PDF em EPUB otimizado para o aparelho alvo.

    Returns:
        Caminho do arquivo EPUB gerado.
    """
    pdf_path = Path(pdf_path).expanduser().resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("O arquivo de entrada precisa ser .pdf")

    if isinstance(device, str):
        key = device.lower().strip()
        if key not in PRESETS:
            raise ValueError(
                f"Aparelho desconhecido: {device}. Opções: {', '.join(PRESETS)}"
            )
        device_preset = PRESETS[key]
    else:
        device_preset = device

    if output_path is None:
        output_path = pdf_path.with_suffix(".epub")
    else:
        output_path = Path(output_path).expanduser().resolve()
        if output_path.is_dir():
            output_path = output_path / f"{pdf_path.stem}.epub"
        elif output_path.suffix.lower() != ".epub":
            output_path = output_path.with_suffix(".epub")

    book = extract_pdf(
        pdf_path,
        max_image_width=device_preset.max_image_width,
        include_images=include_images,
        title_override=title,
        author_override=author,
    )
    return build_epub(book, output_path, device=device_preset)
