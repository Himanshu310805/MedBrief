import re
import logging
import fitz  # PyMuPDF
from app.services.ocr_extraction import ocr_scanned_pdf

logger = logging.getLogger("uvicorn")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text content from PDF file bytes using PyMuPDF (fitz).
    If direct text extraction yields empty/near-empty text (scanned image PDF),
    automatically falls back to ocr_scanned_pdf for OCR processing.

    Args:
        file_bytes (bytes): Binary data of the PDF file.

    Returns:
        str: Extracted text joined page-by-page.

    Raises:
        ValueError: If the PDF data is invalid or cannot be opened.
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.is_encrypted:
            doc.close()
            raise ValueError("The uploaded PDF is password-protected or encrypted. Please upload an unencrypted PDF file.")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Could not read PDF file: file may be corrupted or unreadable ({str(e)})") from e

    extracted_pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()
        if page_text and page_text.strip():
            extracted_pages.append(page_text)

    doc.close()

    direct_text = "\n".join(extracted_pages).strip()

    # Check if direct text extraction yields empty/near-empty text (< 20 non-whitespace chars)
    cleaned_direct = re.sub(r'\s+', '', direct_text)
    if len(cleaned_direct) < 20:
        logger.info("[PDF EXTRACTION] Direct text extraction returned empty/near-empty text. Triggering OCR fallback for scanned PDF...")
        ocr_text = ocr_scanned_pdf(file_bytes)
        return ocr_text if ocr_text else ""

    return direct_text


def extract_text_from_plain_text(text: str) -> str:
    """
    Normalizes plain text input.

    Args:
        text (str): Raw string provided by the user.

    Returns:
        str: Normalized text string.
    """
    if not text:
        return ""
    return text.strip()


def clean_extracted_text(text: str) -> str:
    """
    Cleans extracted medical report text by:
    - Stripping leading and trailing whitespace from each line.
    - Removing non-printable control characters while preserving standard whitespace.
    - Collapsing excessive consecutive blank lines (3 or more newlines to 2).
    - Preserving all clinically relevant medical terms, numbers, and punctuation.

    Args:
        text (str): The raw extracted text.

    Returns:
        str: Cleaned and normalized text.
    """
    if not text:
        return ""

    # Remove non-printable control characters (excluding newline \n, carriage return \r, tab \t)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in cleaned.splitlines()]
    cleaned = "\n".join(lines)

    # Collapse 3+ consecutive newlines down to 2 newlines (double newline / empty line)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()
