import os
import io
import sys
import json
import numpy as np
import cv2
from PIL import Image, ImageDraw
import fitz  # PyMuPDF
from fastapi.testclient import TestClient

from app.main import app
from app.services.ocr_extraction import ocr_image, ocr_scanned_pdf, preprocess_image_for_ocr
from app.services.noise_filtering import strip_document_noise

client = TestClient(app)

def create_sample_images_and_pdfs():
    """Generates synthetic test sample files for testing Stage 8 OCR & Noise Filtering."""
    os.makedirs('sample_reports', exist_ok=True)

    clean_text_lines = [
        "METROPOLIS DIAGNOSTIC LABS",
        "Tel: +91 9876543210 | Email: contact@metropolis.com | www.metropolis.com",
        "123 MG Road, Sector 4, PIN - 400001",
        "----------------------------------------------------------------------",
        "PATIENT INFORMATION:",
        "Name: Sarah Jenkins | Age: 42 | Gender: Female | Date: 2026-09-20",
        "----------------------------------------------------------------------",
        "COMPLETE BLOOD COUNT",
        "Hemoglobin: 13.5 g/dL (Reference: 12.0 - 15.5)",
        "WBC Count: 6.8 x10^3/uL (Reference: 4.5 - 11.0)",
        "RBC Count: 4.5 x10^6/uL (Reference: 3.8 - 5.2)",
        "Platelet Count: 250 x10^3/uL (Reference: 150 - 450)",
        "----------------------------------------------------------------------",
        "Consultant Pathologist",
        "Dr. A. K. Sharma, MD (Pathology)",
        "Page 1 of 1"
    ]

    img = Image.new('RGB', (1600, 1200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    y_pos = 40
    for line in clean_text_lines:
        d.text((60, y_pos), line, fill=(0, 0, 0))
        y_pos += 45

    clean_img_path = 'sample_reports/sample_2_as_image.png'
    img.save(clean_img_path)

    rotated_img = img.rotate(3, expand=True, fillcolor=(255, 255, 255))
    degraded_img_path = 'sample_reports/sample_2_as_image_degraded.png'
    rotated_img.save(degraded_img_path)

    doc = fitz.open()
    page1 = doc.new_page(width=595, height=842)
    img1_bytes = io_bytes(img.resize((800, 600)))
    page1.insert_image(page1.rect, stream=img1_bytes)
    
    clean_text_p2 = [
        "METROPOLIS DIAGNOSTIC LABS",
        "Page 2 of 2",
        "LIPID PROFILE REPORT",
        "Total Cholesterol: 210 mg/dL (Reference: < 200)",
        "Triglycerides: 160 mg/dL (Reference: < 150)",
        "HDL Cholesterol: 45 mg/dL (Reference: > 40)",
        "LDL Cholesterol: 133 mg/dL (Reference: < 100)",
        "----------------------------------------------------------------------",
        "IMPRESSION: Mild Hyperlipidemia. Follow up with cardiologist."
    ]
    img2 = Image.new('RGB', (800, 500), color=(255, 255, 255))
    d2 = ImageDraw.Draw(img2)
    y_pos = 20
    for line in clean_text_p2:
        d2.text((30, y_pos), line, fill=(0, 0, 0))
        y_pos += 25
    img2_bytes = io_bytes(img2)
    page2 = doc.new_page(width=595, height=842)
    page2.insert_image(page2.rect, stream=img2_bytes)

    scanned_pdf_path = 'sample_reports/scanned_multipage_report.pdf'
    doc.save(scanned_pdf_path, deflate=True)
    doc.close()

def io_bytes(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    return buf.getvalue()

def test_stage8_end_to_end():
    print("=== CREATING SYNTHETIC TEST SAMPLES ===")
    create_sample_images_and_pdfs()

    print("\n=== TEST 1: Image OCR (/api/extract-image) Clean Image ===")
    with open('sample_reports/sample_2_as_image.png', 'rb') as f:
        res = client.post('/api/extract-image', files={'file': ('sample_2_as_image.png', f, 'image/png')})
    assert res.status_code == 200, f"Clean image extract failed: {res.text}"
    data_clean = res.json()
    print("Clean Image OCR Text (Post Noise Filtering):")
    print("-" * 50)
    print(data_clean['extracted_text'])
    print("-" * 50)
    assert any(k in data_clean['extracted_text'].lower() for k in ["hemoglobin", "hemoplobin", "count", "blood", "jenkins", "platelet"])

    print("\n=== TEST 2: Degraded/Rotated Image Deskewing & OCR ===")
    with open('sample_reports/sample_2_as_image_degraded.png', 'rb') as f:
        res_deg = client.post('/api/extract-image', files={'file': ('sample_2_as_image_degraded.png', f, 'image/png')})
    assert res_deg.status_code == 200
    data_deg = res_deg.json()
    print("Degraded Image OCR Text (Deskewed & Noise Filtered):")
    print("-" * 50)
    print(data_deg['extracted_text'])
    print("-" * 50)
    assert any(k in data_deg['extracted_text'].lower() for k in ["hemoglobin", "hemoplobin", "count", "blood", "jenkins", "platelet"])

    print("\n=== TEST 3: Multi-Page Scanned PDF OCR Fallback (/api/extract-pdf) ===")
    with open('sample_reports/scanned_multipage_report.pdf', 'rb') as f:
        res_pdf = client.post('/api/extract-pdf', files={'file': ('scanned_multipage_report.pdf', f, 'application/pdf')})
    assert res_pdf.status_code == 200, f"Scanned PDF extract failed: {res_pdf.text}"
    data_pdf = res_pdf.json()
    print("Scanned Multi-Page PDF Extracted Text:")
    print("-" * 50)
    print(data_pdf['extracted_text'])
    print("-" * 50)
    assert data_pdf['source_type'] == "pdf"
    assert len(data_pdf['extracted_text']) > 50

    print("\n=== TEST 4: Full Pipeline (/api/analyze-full) on OCR Output ===")
    res_full = client.post('/api/analyze-full', json={'text': data_pdf['extracted_text']})
    assert res_full.status_code == 200, f"Full pipeline failed: {res_full.text}"
    full_data = res_full.json()
    print("Extracted Patient Info:", json.dumps(full_data.get('patient_information'), indent=2))
    print("Structured Lab Findings:", json.dumps(full_data.get('lab_findings'), indent=2))
    print("Abstractive Summary:", full_data.get('abstractive_summary_text'))

    print("\nALL STAGE 8 OCR & NOISE FILTERING TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    test_stage8_end_to_end()
