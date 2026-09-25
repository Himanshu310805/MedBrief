import json
import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

USER_IMG1 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784527.jpg"
USER_IMG2 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784536.jpg"

def test_final_stage():
    print("=== PART 1 & 2: AUTOMATED ERROR HANDLING & FEATURE TESTS ===")

    # 1. Health Check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("PASS: Health check endpoint working.")

    # 2. Empty Text Input Error Handling
    res = client.post("/api/extract-text", json={"text": "   "})
    assert res.status_code == 400, "Empty text should fail with 400"
    print("PASS: Empty text input handled gracefully (400 Bad Request). Message:", res.json()['detail'])

    # 3. Empty PDF File Error Handling
    res = client.post("/api/extract-pdf", files={'file': ('empty.pdf', b'', 'application/pdf')})
    assert res.status_code == 400, "Empty PDF should fail with 400"
    print("PASS: Empty PDF handled gracefully (400 Bad Request). Message:", res.json()['detail'])

    # 4. Over File Size Limit (>10MB) Error Handling
    oversized_bytes = b'0' * (11 * 1024 * 1024)  # 11 MB
    res = client.post("/api/extract-pdf", files={'file': ('large.pdf', oversized_bytes, 'application/pdf')})
    assert res.status_code == 400, "Oversized file should fail with 400"
    print("PASS: File size limit (>10MB) handled gracefully. Message:", res.json()['detail'])

    # 5. Corrupted PDF Error Handling
    corrupted_bytes = b"%PDF-1.4 corrupted header dummy bytes non-pdf data xyz"
    res = client.post("/api/extract-pdf", files={'file': ('corrupt.pdf', corrupted_bytes, 'application/pdf')})
    assert res.status_code == 400, "Corrupted PDF should fail with 400"
    print("PASS: Corrupted PDF handled gracefully. Message:", res.json()['detail'])

    # 6. Tabular Report Analysis & PDF Report Export Test
    with open(USER_IMG1, 'rb') as f:
        res_extract = client.post("/api/extract-image", files={'file': ('varad.jpg', f, 'image/jpeg')})
    assert res_extract.status_code == 200
    extracted_text = res_extract.json()['extracted_text']

    res_analyze = client.post("/api/analyze-full", json={'text': extracted_text})
    assert res_analyze.status_code == 200
    data = res_analyze.json()
    assert len(data.get('lab_results_table', [])) >= 10

    print(f"PASS: Full Analysis completed with {len(data['lab_results_table'])} laboratory test rows.")

    # 7. Download PDF Report Endpoint Test
    res_pdf = client.post("/api/download-report", json=data)
    assert res_pdf.status_code == 200, f"PDF Download failed: {res_pdf.text}"
    assert res_pdf.headers["content-type"] == "application/pdf"
    pdf_content = res_pdf.content
    assert pdf_content.startswith(b"%PDF-"), "Invalid PDF binary format"
    print(f"PASS: PDF Download endpoint generated valid PDF ({len(pdf_content)} bytes). Header: {pdf_content[:8]}")

    print("\nALL STAGE 10 BACKEND TESTS PASSED 100% PERFECTLY!")

if __name__ == '__main__':
    test_final_stage()
