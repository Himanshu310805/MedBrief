import io
import os
import logging
import numpy as np
import cv2
from PIL import Image
import pytesseract
import pdf2image
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
)

logger = logging.getLogger("uvicorn")

DEBUG_DIR = "debug_ocr_output"


def compute_ocr_confidence_and_text(image: Image.Image):
    """
    Computes average Tesseract word confidence score and extracts text.

    Args:
        image (Image.Image): PIL Image object.

    Returns:
        tuple: (avg_confidence: float, text: str)
    """
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(image)
        
        confidences = []
        if 'text' in data and 'conf' in data:
            for i in range(len(data['text'])):
                word = str(data['text'][i]).strip()
                try:
                    conf = int(data['conf'][i])
                except (ValueError, TypeError):
                    conf = -1
                
                if conf > 0 and len(word) > 0:
                    confidences.append(conf)
        
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        return avg_conf, text.strip() if text else ""
    except Exception as e:
        logger.warning(f"Confidence score calculation error: {e}")
        try:
            fallback_text = pytesseract.image_to_string(image)
            return 50.0, fallback_text.strip() if fallback_text else ""
        except Exception:
            return 0.0, ""


def preprocess_image_for_ocr(image: Image.Image, debug: bool = False, prefix: str = "ocr") -> Image.Image:
    """
    Preprocesses an image using OpenCV for Tesseract OCR.
    Optionally dumps intermediate debug images to debug_ocr_output/ if debug=True.

    Args:
        image (Image.Image): Input PIL Image.
        debug (bool): If True, saves intermediate images.
        prefix (str): Prefix for debug filenames.

    Returns:
        Image.Image: Preprocessed PIL Image.
    """
    if debug:
        os.makedirs(DEBUG_DIR, exist_ok=True)
        image.save(os.path.join(DEBUG_DIR, f"{prefix}_00_original.png"))

    # 1. Upscale low-resolution images
    w, h = image.size
    if w < 1200:
        scale_factor = 2.0
        image = image.resize((int(w * scale_factor), int(h * scale_factor)), Image.Resampling.LANCZOS)

    img_np = np.array(image.convert("RGB"))

    # 2. Convert to grayscale
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    if debug:
        cv2.imwrite(os.path.join(DEBUG_DIR, f"{prefix}_01_grayscale.png"), gray)

    # 3. Deskewing (using correct (x, y) point coordinates for minAreaRect)
    gray_deskewed = gray.copy()
    try:
        thresh_inv = cv2.threshold(gray_deskewed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh_inv > 0))
        if len(coords) > 100:
            # Fix: OpenCV minAreaRect requires (x, y) coordinates, not (y, x)
            pts = np.zeros((len(coords), 2), dtype=np.float32)
            pts[:, 0] = coords[:, 1]  # x = cols
            pts[:, 1] = coords[:, 0]  # y = rows
            
            rect = cv2.minAreaRect(pts)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle

            # Only deskew if slight tilt detected (between 1.0 and 15.0 degrees)
            if 1.0 <= abs(angle) <= 15.0:
                (h_g, w_g) = gray_deskewed.shape[:2]
                center = (w_g // 2, h_g // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray_deskewed = cv2.warpAffine(
                    gray_deskewed, M, (w_g, h_g), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
                )
    except Exception as skew_err:
        logger.warning(f"Deskewing step skipped: {skew_err}")

    if debug:
        cv2.imwrite(os.path.join(DEBUG_DIR, f"{prefix}_02_deskewed.png"), gray_deskewed)

    # 4. Contrast enhancement (CLAHE) + Otsu Binarization (replaces buggy fixed-block adaptive thresholding)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray_deskewed)
    _, thresholded = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    if debug:
        cv2.imwrite(os.path.join(DEBUG_DIR, f"{prefix}_03_thresholded.png"), thresholded)

    if debug:
        cv2.imwrite(os.path.join(DEBUG_DIR, f"{prefix}_04_final.png"), thresholded)

    return Image.fromarray(thresholded)


def ocr_image(image_bytes: bytes, debug: bool = False, prefix: str = "ocr") -> str:
    """
    Processes an image file (PNG/JPG/JPEG) with Dual-Pass Confidence Selection for maximum OCR accuracy.

    Pass 1: Raw Grayscale Image (upscaled)
    Pass 2: Preprocessed Image (CLAHE + Otsu Binarization + Deskew)

    Compares average Tesseract word confidence scores and returns the output from the superior pass.

    Args:
        image_bytes (bytes): Binary bytes of the image file.
        debug (bool): If True, saves intermediate debug images.
        prefix (str): Prefix for debug images.

    Returns:
        str: Extracted raw text content.

    Raises:
        ValueError: If Tesseract is not installed on system PATH or image is invalid.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Could not open image file: {str(e)}") from e

    # Pass 1: Raw Grayscale (scaled up if low-res)
    w, h = image.size
    if w < 1200:
        scale_factor = 2.0
        scaled_image = image.resize((int(w * scale_factor), int(h * scale_factor)), Image.Resampling.LANCZOS)
    else:
        scaled_image = image

    gray_np = cv2.cvtColor(np.array(scaled_image.convert("RGB")), cv2.COLOR_RGB2GRAY)
    gray_pil = Image.fromarray(gray_np)

    conf_gray, text_gray = compute_ocr_confidence_and_text(gray_pil)

    # Pass 2: Enhanced Preprocessed Image
    preprocessed_pil = preprocess_image_for_ocr(image, debug=debug, prefix=prefix)
    conf_prep, text_prep = compute_ocr_confidence_and_text(preprocessed_pil)

    logger.info(f"[OCR DUAL-PASS] Pass 1 (Grayscale) Conf: {conf_gray:.2f}% | Pass 2 (Preprocessed) Conf: {conf_prep:.2f}%")

    # Select best pass based on confidence and text length
    if conf_prep > (conf_gray + 5.0) and len(text_prep) >= len(text_gray) * 0.7:
        selected_text = text_prep
        logger.info("[OCR DUAL-PASS] Selected Pass 2 (Preprocessed).")
    else:
        selected_text = text_gray
        logger.info("[OCR DUAL-PASS] Selected Pass 1 (Grayscale).")

    return selected_text if selected_text else ""


def ocr_scanned_pdf(pdf_bytes: bytes, debug: bool = False) -> str:
    """
    Converts each page of a scanned PDF to an image using pdf2image (poppler),
    runs Dual-Pass OCR on each page, and joins results.

    Args:
        pdf_bytes (bytes): Binary data of the PDF file.
        debug (bool): If True, dumps debug images.

    Returns:
        str: Extracted text joined page-by-page.

    Raises:
        ValueError: If Poppler or Tesseract is missing on system PATH, or PDF is corrupted.
    """
    try:
        page_images = pdf2image.convert_from_bytes(pdf_bytes)
    except (PDFInfoNotInstalledError, FileNotFoundError) as e:
        raise ValueError(
            "Poppler utility (pdf2image backend) was not found on the system PATH. "
            "Please install Poppler and ensure 'pdftoppm' is accessible on your system environment PATH."
        ) from e
    except (PDFPageCountError, PDFSyntaxError) as e:
        raise ValueError(f"Could not process PDF pages with Poppler: {str(e)}") from e
    except Exception as e:
        err_msg = str(e)
        if "poppler" in err_msg.lower() or "pdftoppm" in err_msg.lower():
            raise ValueError(
                "Poppler utility was not found on the system PATH. "
                "Please install Poppler and ensure 'pdftoppm' is added to system PATH."
            ) from e
        raise ValueError(f"Failed to convert PDF to images: {err_msg}") from e

    if not page_images:
        return ""

    extracted_pages = []
    for page_idx, page_img in enumerate(page_images):
        try:
            # Pass PIL image bytes to ocr_image
            buf = io.BytesIO()
            page_img.save(buf, format="PNG")
            page_text = ocr_image(buf.getvalue(), debug=debug, prefix=f"pdf_page_{page_idx+1}")
            if page_text and page_text.strip():
                extracted_pages.append(page_text.strip())
        except (pytesseract.TesseractNotFoundError, FileNotFoundError) as e:
            raise ValueError(
                "Tesseract OCR binary engine was not found on the system PATH. "
                "Please install Tesseract-OCR and ensure it is added to your system environment PATH."
            ) from e
        except Exception as e:
            logger.warning(f"OCR failed on page {page_idx + 1}: {e}")

    return "\n\n".join(extracted_pages)
