import os
import io
import cv2
import numpy as np
from PIL import Image
import pytesseract

DEBUG_DIR = "debug_ocr_output"
os.makedirs(DEBUG_DIR, exist_ok=True)

USER_IMG1 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784527.jpg"
USER_IMG2 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784536.jpg"

def debug_step1(image_path: str, prefix: str):
    print(f"\n=================== DEBUGGING {prefix} ===================")
    pil_img = Image.open(image_path)
    
    # 00 Original
    path_00 = os.path.join(DEBUG_DIR, f"{prefix}_00_original.png")
    pil_img.save(path_00)
    print(f"Saved {path_00}, size={pil_img.size}")

    # 1. Upscale if low resolution
    w, h = pil_img.size
    if w < 1200:
        scale_factor = 2.0
        pil_img = pil_img.resize((int(w * scale_factor), int(h * scale_factor)), Image.Resampling.LANCZOS)

    img_np = np.array(pil_img.convert("RGB"))

    # 01 Grayscale
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    path_01 = os.path.join(DEBUG_DIR, f"{prefix}_01_grayscale.png")
    cv2.imwrite(path_01, gray)
    print(f"Saved {path_01}, shape={gray.shape}")

    # 02 Deskewed (current logic)
    gray_deskewed = gray.copy()
    skew_angle = 0
    try:
        thresh_inv = cv2.threshold(gray_deskewed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh_inv > 0))
        if len(coords) > 0:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            else:
                angle = -angle
            skew_angle = angle
            if 0.5 < abs(angle) < 45.0:
                (h_g, w_g) = gray_deskewed.shape[:2]
                center = (w_g // 2, h_g // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray_deskewed = cv2.warpAffine(
                    gray_deskewed, M, (w_g, h_g), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
                )
    except Exception as e:
        print("Deskew error:", e)

    path_02 = os.path.join(DEBUG_DIR, f"{prefix}_02_deskewed.png")
    cv2.imwrite(path_02, gray_deskewed)
    print(f"Saved {path_02}, detected_skew_angle={skew_angle}")

    # 03 Thresholded (current adaptive threshold with blockSize=11)
    adaptive_thresh = cv2.adaptiveThreshold(
        gray_deskewed, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    path_03 = os.path.join(DEBUG_DIR, f"{prefix}_03_thresholded.png")
    cv2.imwrite(path_03, adaptive_thresh)
    print(f"Saved {path_03}")

    # 04 Final (current fastNlMeansDenoising)
    try:
        denoised = cv2.fastNlMeansDenoising(adaptive_thresh, h=10)
    except Exception:
        denoised = adaptive_thresh
    path_04 = os.path.join(DEBUG_DIR, f"{prefix}_04_final.png")
    cv2.imwrite(path_04, denoised)
    print(f"Saved {path_04}")

    # Run OCR on Current Final vs Raw Grayscale
    final_pil = Image.fromarray(denoised)
    ocr_current = pytesseract.image_to_string(final_pil)

    gray_pil = Image.fromarray(gray)
    ocr_raw_gray = pytesseract.image_to_string(gray_pil)

    print("\n--- OCR OUTPUT FROM CURRENT PREPROCESSED FINAL (04_final.png) ---")
    print(ocr_current[:500] if ocr_current else "[EMPTY / GIBBERISH]")

    print("\n--- OCR OUTPUT FROM RAW GRAYSCALE (01_grayscale.png) ---")
    print(ocr_raw_gray[:500] if ocr_raw_gray else "[EMPTY]")

if __name__ == "__main__":
    debug_step1(USER_IMG1, "varad_lab")
    debug_step1(USER_IMG2, "care_lab")
