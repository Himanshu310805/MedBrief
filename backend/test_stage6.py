import time
import json
import logging
from fastapi.testclient import TestClient
from app.main import app

# Configure logging to capture uvicorn pipeline timing logs
logging.basicConfig(level=logging.INFO)
client = TestClient(app)

def test_full_pipeline():
    with open('sample_reports/sample_report_01.txt', 'r', encoding='utf-8') as f:
        sample_text = f.read()

    print("=== TESTING POST /api/analyze-full ===")
    
    t0 = time.time()
    response = client.post("/api/analyze-full", json={"text": sample_text})
    t_total = round(time.time() - t0, 4)
    
    print(f"HTTP Status Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    res_data = response.json()
    
    print(f"Total Client Execution Time: {t_total}s\n")
    print("=== FULL STRUCTURED SUMMARY RESPONSE ===")
    print(json.dumps(res_data, indent=2))
    
    # Assertions
    assert res_data["success"] is True
    assert res_data["patient_information"]["patient_name"] == "John Doe (Synthetic)"
    assert res_data["symptoms"]["verified"] is True
    assert res_data["diagnosis_conditions"]["verified"] is True
    assert res_data["medications"]["verified"] is True
    assert res_data["lab_findings"]["verified"] is True
    assert res_data["procedures"]["verified"] is True
    assert res_data["follow_up"]["content"] != "Not mentioned"
    assert res_data["follow_up"]["verified"] is True

    print("\nALL STAGE 6 VERIFICATION ASSERTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_full_pipeline()
