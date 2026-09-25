import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_abstractive_summary_endpoint():
    with open('sample_reports/sample_report_01.txt', 'r', encoding='utf-8') as f:
        sample_text = f.read()

    print("=== TESTING POST /api/summarize-abstractive ===")
    
    # Test 1: Normal input report
    payload = {
        "text": sample_text,
        "max_length": 150,
        "min_length": 40
    }
    response = client.post("/api/summarize-abstractive", json=payload)
    print("Status Code:", response.status_code)
    res_data = response.json()
    print("Response JSON:")
    for k, v in res_data.items():
        print(f"  {k}: {v}")

    assert response.status_code == 200
    assert res_data["success"] is True
    assert len(res_data["abstractive_summary"]) > 0
    assert res_data["chunks_processed"] == 1
    assert res_data["model_used"] == "sshleifer/distilbart-cnn-6-6"
    assert res_data["input_word_count"] > 0
    assert res_data["processing_time_seconds"] > 0.0

    # Test 2: Empty text edge case
    empty_res = client.post("/api/summarize-abstractive", json={"text": ""})
    print("\nEmpty Text Status Code:", empty_res.status_code)
    assert empty_res.status_code == 400

    # Test 3: Short text warning edge case
    short_res = client.post("/api/summarize-abstractive", json={"text": "Patient has mild chest pain and shortness of breath."})
    print("\nShort Text Status Code:", short_res.status_code)
    short_data = short_res.json()
    print("Short Text Warning:", short_data.get("warning"))
    assert short_res.status_code == 200
    assert short_data["warning"] is not None

    print("\nALL API ENDPOINT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_abstractive_summary_endpoint()
