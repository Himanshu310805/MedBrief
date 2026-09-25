import json
from app.services.ocr_extraction import ocr_image
from app.services.noise_filtering import strip_document_noise
from app.services.table_to_narrative import detect_tabular_lab_data

USER_IMG1 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784527.jpg"
USER_IMG2 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784536.jpg"

def debug_report(image_path, label):
    print(f"\n=================== DEBUGGING TABLE PARSING FOR {label} ===================")
    with open(image_path, 'rb') as f:
        raw_ocr = ocr_image(f.read())
    
    cleaned = strip_document_noise(raw_ocr)
    print("\n--- CLEANED TEXT LINES ---")
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    for idx, line in enumerate(lines):
        print(f"Line {idx+1:02d}: {line}")

    rows = detect_tabular_lab_data(cleaned)
    print(f"\n--- DETECTED TABLE ROWS (COUNT = {len(rows)}) ---")
    for r in rows:
        print(r)

if __name__ == '__main__':
    debug_report(USER_IMG1, "Varad Pathology Lab")
    debug_report(USER_IMG2, "Care Pathology Lab")
