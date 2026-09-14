"""CLI: converter PDF → EPUB para Xteink X3."""

from __future__ import annotations

from pathlib import Path

import click

from converter import convert_pdf_to_epub
from converter.device import PRESETS


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("pdf", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Arquivo ou pasta de saída (.epub).",
)
@click.option(
    "-d",
    "--device",
    type=click.Choice(sorted(PRESETS.keys()), case_sensitive=False),
    default="x3",
    show_default=True,
    help="Preset do aparelho (otimiza CSS e imagens).",
)
@click.option("--title", default=None, help="Título do livro (sobrescreve metadados do PDF).")
@click.option("--author", default=None, help="Autor (sobrescreve metadados do PDF).")
@click.option(
    "--no-images",
    is_flag=True,
    help="Não incluir imagens (EPUB mais leve, só texto).",
)
def main(
    pdf: Path,
    output: Path | None,
    device: str,
    title: str | None,
    author: str | None,
    no_images: bool,
) -> None:
    """Converte PDF em EPUB otimizado para Xteink X3 (3.7\" / 528×792)."""
    out = convert_pdf_to_epub(
        pdf,
        output,
        device=device,
        include_images=not no_images,
        title=title,
        author=author,
    )
    preset = PRESETS[device.lower()]
    click.echo(f"OK -> {out}")
    click.echo(
        f"Otimizado para {preset.name} "
        f"({preset.width_px}x{preset.height_px}, {preset.screen_inch}\")"
    )
    click.echo("Copie o .epub para o cartao microSD (pasta do Xteink) ou envie pelo app.")


if __name__ == "__main__":
    main()
