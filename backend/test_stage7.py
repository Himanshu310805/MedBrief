import time
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_evaluation_pipeline():
    with open('sample_reports/sample_report_01.txt', 'r', encoding='utf-8') as f:
        sample_report = f.read()

    with open('sample_reports/sample_reference_summary.txt', 'r', encoding='utf-8') as f:
        reference_summary = f.read()

    print("=== STEP 1: Calling POST /api/analyze-full to get generated summaries ===")
    t0 = time.time()
    full_res = client.post("/api/analyze-full", json={"text": sample_report})
    assert full_res.status_code == 200, f"Failed /api/analyze-full: {full_res.text}"
    full_data = full_res.json()
    
    extractive_text = full_data["extractive_summary_text"]
    abstractive_text = full_data["abstractive_summary_text"]

    print(f"Extractive Summary: {extractive_text}\n")
    print(f"Abstractive Summary: {abstractive_text}\n")
    print(f"Reference Summary: {reference_summary}\n")

    print("=== STEP 2: Calling POST /api/evaluate ===")
    t1 = time.time()
    eval_res = client.post(
        "/api/evaluate",
        json={
            "extractive_summary": extractive_text,
            "abstractive_summary": abstractive_text,
            "reference_summary": reference_summary
        }
    )
    assert eval_res.status_code == 200, f"Failed /api/evaluate: {eval_res.text}"
    eval_data = eval_res.json()

    print("=== ROUGE EVALUATION RESPONSE ===")
    print(json.dumps(eval_data, indent=2))

    assert eval_data["success"] is True
    assert "rouge1" in eval_data["extractive_scores"]
    assert "rouge1" in eval_data["abstractive_scores"]
    assert len(eval_data["comparison_note"]) > 0

    print("\nALL STAGE 7 ROUGE EVALUATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_evaluation_pipeline()
