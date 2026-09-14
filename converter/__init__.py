"""Conversor PDF → EPUB otimizado para Xteink X3."""

from .convert import convert_pdf_to_epub
from .device import XTEINK_X3

__all__ = ["convert_pdf_to_epub", "XTEINK_X3"]
