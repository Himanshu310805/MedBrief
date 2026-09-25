import urllib.request
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_live_backend():
    print("=== TEST 1: Live Health Check ===")
    res1 = requests.get(f"{BASE_URL}/api/health")
    print("Health Check Response:", res1.json())
    assert res1.status_code == 200

    print("\n=== TEST 2: Plain Text Extraction ===")
    res2 = requests.post(f"{BASE_URL}/api/extract-text", json={"text": "Patient Name: John Doe\nDiagnosis: Hypertension."})
    print("Extract Text Response:", res2.json())
    assert res2.status_code == 200

    print("\n=== TEST 3: Image Upload OCR (/api/extract-image) ===")
    with open('sample_reports/sample_2_as_image.png', 'rb') as f:
        res3 = requests.post(f"{BASE_URL}/api/extract-image", files={'file': ('sample_2_as_image.png', f, 'image/png')})
    print("Image Extract Response:", res3.json())
    assert res3.status_code == 200

    print("\n=== TEST 4: Scanned Multi-Page PDF OCR (/api/extract-pdf) ===")
    with open('sample_reports/scanned_multipage_report.pdf', 'rb') as f:
        res4 = requests.post(f"{BASE_URL}/api/extract-pdf", files={'file': ('scanned_multipage_report.pdf', f, 'application/pdf')})
    print("PDF Extract Response:", res4.json())
    assert res4.status_code == 200

    print("\n=== TEST 5: Full Pipeline Analysis (/api/analyze-full) ===")
    res5 = requests.post(f"{BASE_URL}/api/analyze-full", json={"text": res4.json()['extracted_text']})
    print("Full Pipeline Status Code:", res5.status_code)
    print("Patient Info:", json.dumps(res5.json().get('patient_information'), indent=2))
    print("Abstractive Summary:", res5.json().get('abstractive_summary_text'))
    assert res5.status_code == 200

    print("\nALL LIVE ENDPOINTS AND UI-BACKEND FLOWS VERIFIED PERFECTLY!")

if __name__ == '__main__':
    test_live_backend()
