"""
Converter registry package.
"""
from .base import BaseConverter
from .html_conv import HTMLConverter
from .json_conv import StructuredDataConverter
from .sheet_conv import SheetConverter
from .doc_conv import DocxConverter
from .pdf_conv import PDFConverter
from .code_conv import CodeConverter
from .text_conv import TextConverter

ALL_CONVERTERS = [
    HTMLConverter(),
    StructuredDataConverter(),
    SheetConverter(),
    DocxConverter(),
    PDFConverter(),
    CodeConverter(),
    TextConverter(), # fallback text converter is last
]

def get_converter_for_file(filepath: str) -> BaseConverter:
    for conv in ALL_CONVERTERS:
        if conv.can_handle(filepath):
            return conv
    return TextConverter()
