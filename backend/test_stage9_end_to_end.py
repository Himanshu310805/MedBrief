import json
from fastapi.testclient import TestClient
from app.main import app

USER_IMG1 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784527.jpg"
USER_IMG2 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784536.jpg"

def test_stage9():
    client = TestClient(app)
    
    print("=== TEST 1: Health Check ===")
    res_health = client.get("/api/health")
    assert res_health.status_code == 200, f"Health check failed: {res_health.text}"
    print("Health check status:", res_health.json())

    print("\n=== TEST 2: Tabular Report OCR & Analysis (Varad Pathology Lab) ===")
    with open(USER_IMG1, 'rb') as f:
        res_extract = client.post("/api/extract-image", files={'file': ('varad.jpg', f, 'image/jpeg')})
    assert res_extract.status_code == 200, f"Extraction failed: {res_extract.text}"
    extracted_text = res_extract.json()['extracted_text']

    res_analyze = client.post("/api/analyze-full", json={'text': extracted_text})
    assert res_analyze.status_code == 200, f"Analysis failed: {res_analyze.text}"
    data = res_analyze.json()

    print(f"Total Table Rows Parsed: {len(data.get('lab_results_table', []))}")
    print("\nParsed Lab Results Table:")
    print(json.dumps(data.get('lab_results_table'), indent=2))
    print("\nCleaned Other Clinical Observations:")
    print(json.dumps(data.get('other_observations'), indent=2))

    # Verify no administrative / contact rows in lab_results_table
    for row in data.get('lab_results_table', []):
        name = row.get('test_name', '').lower()
        assert 'reg. no' not in name and 'registration' not in name, f"Found admin label in table: {name}"

    assert len(data.get('lab_results_table', [])) >= 10, "Failed to parse expected table rows"

    print("\n=== TEST 3: Tabular Report OCR & Analysis (Care Pathology Lab) ===")
    with open(USER_IMG2, 'rb') as f:
        res_extract2 = client.post("/api/extract-image", files={'file': ('care.jpg', f, 'image/jpeg')})
    assert res_extract2.status_code == 200
    extracted_text2 = res_extract2.json()['extracted_text']

    res_analyze2 = client.post("/api/analyze-full", json={'text': extracted_text2})
    assert res_analyze2.status_code == 200
    data2 = res_analyze2.json()

    print(f"Total Table Rows Parsed (Care): {len(data2.get('lab_results_table', []))}")
    print("\nParsed Lab Results Table (Care):")
    print(json.dumps(data2.get('lab_results_table'), indent=2))

    for row in data2.get('lab_results_table', []):
        name = row.get('test_name', '').lower()
        assert 'reg. no' not in name and 'registration' not in name, f"Found admin label in table: {name}"

    assert len(data2.get('lab_results_table', [])) >= 10, "Failed to parse expected table rows for Care lab"

    print("\n=== TEST 4: Non-Tabular Narrative Report (Backward Compatibility Check) ===")
    plain_narrative = (
        "PATIENT INFORMATION: John Doe, 54M. CHIEF COMPLAINT: Patient reports shortness of breath on exertion. "
        "DIAGNOSIS: Essential hypertension and hyperlipidemia. "
        "TREATMENT PLAN: Initiate Lisinopril 10 mg daily and Atorvastatin 20 mg. Follow-up in 4 weeks."
    )
    res_plain = client.post("/api/analyze-full", json={'text': plain_narrative})
    assert res_plain.status_code == 200
    data_plain = res_plain.json()
    print("Non-Tabular Lab Table Length:", len(data_plain.get('lab_results_table', [])))
    print("Non-Tabular Lab Findings Content:", data_plain.get('lab_findings'))
    assert len(data_plain.get('lab_results_table', [])) == 0, "Non-tabular report should have empty lab table"

    print("\nALL END-TO-END TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    test_stage9()
