import os
import json
from app.services.ocr_extraction import ocr_image
from app.services.noise_filtering import strip_document_noise

USER_IMG1 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784527.jpg"
USER_IMG2 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784536.jpg"

def run_test(image_path: str, label: str, prefix: str):
    print(f"\n=================== TESTING REAL PHOTO: {label} ===================")
    with open(image_path, 'rb') as f:
        img_bytes = f.read()
    
    raw_ocr = ocr_image(img_bytes, debug=True, prefix=prefix)
    noise_stripped = strip_document_noise(raw_ocr)

    print(f"\n--- RAW OCR TEXT ({label}) ---")
    print(raw_ocr)
    print("\n--- NOISE FILTERED OCR TEXT ---")
    print(noise_stripped)

if __name__ == '__main__':
    run_test(USER_IMG1, "Varad Pathology Lab", "varad_lab")
    run_test(USER_IMG2, "Care Pathology Lab", "care_lab")

    debug_files = os.listdir("debug_ocr_output")
    print("\n=== DUMPED DEBUG IMAGES IN backend/debug_ocr_output/ ===")
    for fname in sorted(debug_files):
        print(f" - {fname}")
