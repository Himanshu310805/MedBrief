import os
import io
import cv2
import numpy as np
from PIL import Image
import pytesseract

USER_IMG1 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784527.jpg"
USER_IMG2 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784536.jpg"

def get_ocr_confidence_and_text(image: Image.Image):
    """
    Runs pytesseract.image_to_data on PIL image and computes:
    1. Average confidence score of valid extracted words (conf > 0).
    2. Extracted full text string.
    """
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(image)
        confidences = []
        for i in range(len(data['text'])):
            word = data['text'][i].strip()
            conf = int(data['conf'][i])
            if conf > 0 and len(word) > 0:
                confidences.append(conf)
        
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        return avg_conf, text.strip() if text else ""
    except Exception as e:
        return 0.0, ""

def preprocess_improved(image: Image.Image) -> Image.Image:
    """
    Improved preprocessing pipeline:
    1. Grayscale
    2. Dynamic Otsu Binarization / Contrast Enhancement (CLAHE) instead of fixed block-11 adaptive threshold
    """
    w, h = image.size
    if w < 1200:
        scale_factor = 2.0
        image = image.resize((int(w * scale_factor), int(h * scale_factor)), Image.Resampling.LANCZOS)

    img_np = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Otsu thresholding
    _, otsu_thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return Image.fromarray(otsu_thresh)

def test_dual_pass_ocr(image_path: str, label: str):
    print(f"\n=================== TESTING DUAL-PASS OCR FOR {label} ===================")
    pil_img = Image.open(image_path)

    # Pass 1: Raw Grayscale Image
    w, h = pil_img.size
    if w < 1200:
        scale_factor = 2.0
        scaled_img = pil_img.resize((int(w * scale_factor), int(h * scale_factor)), Image.Resampling.LANCZOS)
    else:
        scaled_img = pil_img

    gray_np = cv2.cvtColor(np.array(scaled_img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    gray_pil = Image.fromarray(gray_np)

    conf_gray, text_gray = get_ocr_confidence_and_text(gray_pil)

    # Pass 2: Enhanced Preprocessed Image
    preprocessed_pil = preprocess_improved(pil_img)
    conf_prep, text_prep = get_ocr_confidence_and_text(preprocessed_pil)

    print(f"Pass 1 (Raw Grayscale) Confidence Score: {conf_gray:.2f}%")
    print(f"Pass 2 (Preprocessed Otsu) Confidence Score: {conf_prep:.2f}%")

    if conf_prep > conf_gray and len(text_prep) > len(text_gray) * 0.5:
        selected_pass = "Pass 2 (Preprocessed)"
        final_text = text_prep
    else:
        selected_pass = "Pass 1 (Raw Grayscale)"
        final_text = text_gray

    print(f"--> SELECTED BEST PASS: {selected_pass}")
    print("\n--- FINAL EXTRACTED TEXT ---")
    print(final_text)

if __name__ == '__main__':
    test_dual_pass_ocr(USER_IMG1, "Varad Pathology Lab")
    test_dual_pass_ocr(USER_IMG2, "Care Pathology Lab")
