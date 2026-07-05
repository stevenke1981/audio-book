"""Multi-format text extraction for audiobook conversion."""

from __future__ import annotations

import logging
import re
import zipfile
from html import unescape
from pathlib import Path
from typing import Callable, List, Optional

import PyPDF2
import ebooklib
from ebooklib import epub

logger = logging.getLogger(__name__)

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import docx2txt

    DOC_AVAILABLE = True
except ImportError:
    DOC_AVAILABLE = False

try:
    from bs4 import BeautifulSoup

    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False


class TextExtractor:
    """Extract and clean text from supported document formats."""

    def __init__(
        self,
        clean_page_numbers: bool = True,
        normalize_whitespace: bool = True,
    ):
        self.clean_page_numbers = clean_page_numbers
        self.normalize_whitespace = normalize_whitespace

    def extract(self, file_path: Path) -> str:
        extension = file_path.suffix.lower()
        handlers = {
            ".txt": self._extract_txt,
            ".pdf": self._extract_pdf,
            ".epub": self.extract_from_epub,
            ".docx": self._extract_docx,
            ".doc": self._extract_doc,
        }
        handler = handlers.get(extension)
        if not handler:
            raise ValueError(f"Unsupported file format: {extension}")
        return handler(file_path)

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        if self.clean_page_numbers:
            # Remove line-isolated page numbers BEFORE whitespace normalization.
            # Uses MULTILINE mode so ^/$ match line boundaries.
            # Only removes entire lines consisting solely of 1-3 digits.
            # This avoids removing chapter numbers ("Chapter 42"), years ("2025"), or inline data.
            text = re.sub(r"^\d{1,3}$", "", text, flags=re.MULTILINE)
        if self.normalize_whitespace:
            text = re.sub(r"\s+", " ", text)
            text = text.replace("\n", " ")
        return text.strip()

    def clean_html(self, html_content: str) -> str:
        if not html_content:
            return ""

        if BS4_AVAILABLE:
            try:
                soup = BeautifulSoup(html_content, "html.parser")
                for tag in soup(["script", "style"]):
                    tag.decompose()
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                return " ".join(chunk for chunk in chunks if chunk)
            except Exception:
                pass

        html_content = re.sub(
            r"<style[^>]*>.*?</style>", "", html_content, flags=re.DOTALL | re.IGNORECASE
        )
        html_content = re.sub(
            r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE
        )
        html_content = re.sub(r"<[^>]+>", " ", html_content)
        html_content = unescape(html_content)
        html_content = re.sub(r"\s+", " ", html_content)
        return html_content.strip()

    def _extract_txt(self, file_path: Path) -> str:
        for encoding in ("utf-8", "utf-16", "latin-1", "cp1252"):
            try:
                with open(file_path, encoding=encoding) as f:
                    return self.clean_text(f.read())
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not decode text file")

    def _extract_pdf(self, file_path: Path) -> str:
        text = ""
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            logger.info("PDF has %d pages", total_pages)

            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += f"\n\n{page_text}"
                    if page_num % 10 == 0:
                        logger.debug("Extracted %d/%d pages", page_num, total_pages)
                except Exception as exc:
                    logger.warning("Failed to extract page %d: %s", page_num, exc)

            logger.info(
                "Extracted text from %d pages, %d characters total",
                total_pages,
                len(text),
            )
        return self.clean_text(text)

    def extract_from_epub(self, file_path: Path) -> str:
        methods: List[Callable[[Path], str]] = [
            self._extract_epub_ebooklib,
            self._extract_epub_zipfile,
            self._extract_epub_manual,
        ]
        for method in methods:
            try:
                text = method(file_path)
                if text and text.strip():
                    logger.info("EPUB extraction successful: %d characters", len(text))
                    return text
            except Exception as exc:
                logger.warning("EPUB method %s failed: %s", method.__name__, exc)
        raise RuntimeError("All EPUB extraction methods failed")

    def _extract_epub_ebooklib(self, file_path: Path) -> str:
        book = epub.read_epub(str(file_path))
        text_parts: List[str] = []

        for item_id, _linear in book.spine:
            try:
                item = book.get_item_by_id(item_id)
                if item and isinstance(item, ebooklib.ITEM_DOCUMENT):
                    content = item.get_body_content()
                    if content:
                        if isinstance(content, bytes):
                            content = content.decode("utf-8", errors="ignore")
                        clean_text = self.clean_html(str(content))
                        if clean_text.strip():
                            text_parts.append(clean_text)
            except Exception:
                continue

        return "\n\n".join(text_parts)

    def _extract_epub_zipfile(self, file_path: Path) -> str:
        text_parts: List[str] = []
        with zipfile.ZipFile(file_path, "r") as epub_zip:
            for file_name in epub_zip.namelist():
                if file_name.lower().endswith((".html", ".xhtml", ".htm")):
                    try:
                        content = epub_zip.read(file_name).decode("utf-8", errors="ignore")
                        clean_text = self.clean_html(content)
                        if clean_text.strip():
                            text_parts.append(clean_text)
                    except Exception:
                        continue
        return "\n\n".join(text_parts)

    def _extract_epub_manual(self, file_path: Path) -> str:
        text_parts: List[str] = []
        skip_ext = (".jpg", ".jpeg", ".png", ".gif", ".css", ".js")
        with zipfile.ZipFile(file_path, "r") as epub_zip:
            for file_name in epub_zip.namelist():
                if not any(file_name.lower().endswith(ext) for ext in skip_ext):
                    try:
                        content = epub_zip.read(file_name).decode("utf-8", errors="ignore")
                        if "<" in content and len(content.strip()) > 100:
                            clean_text = self.clean_html(content)
                            if clean_text:
                                text_parts.append(clean_text)
                    except Exception:
                        continue
        return "\n\n".join(text_parts)

    def _extract_docx(self, file_path: Path) -> str:
        if not DOCX_AVAILABLE:
            raise ValueError("python-docx is required for .docx files")
        doc = Document(file_path)
        text = "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
        return self.clean_text(text)

    def _extract_doc(self, file_path: Path) -> str:
        if not DOC_AVAILABLE:
            raise ValueError("docx2txt is required for .doc files")
        text = docx2txt.process(str(file_path))
        return self.clean_text(text) if text else ""

    def get_supported_formats(self) -> List[str]:
        formats = [".txt", ".pdf", ".epub"]
        if DOCX_AVAILABLE:
            formats.append(".docx")
        if DOC_AVAILABLE:
            formats.append(".doc")
        return formats