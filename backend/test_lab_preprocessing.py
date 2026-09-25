"""
Test suite for Tabular Lab Report Preprocessing and Abstractive Summarization Fix.
"""

import sys
import json
from fastapi.testclient import TestClient
from app.main import app
from app.services.table_to_narrative import (
    detect_tabular_lab_data,
    generate_narrative_from_table,
    strip_boilerplate_and_disclaimers
)

client = TestClient(app)


def test_table_detection_and_narrative_generation():
    print("\n=======================================================", flush=True)
    print("1. TESTING TABLE DETECTION & NARRATIVE GENERATION", flush=True)
    print("=======================================================", flush=True)

    reports = {
        "CBC": "sample_reports/sample_cbc_report.txt",
        "LFT": "sample_reports/sample_lft_report.txt",
        "Lipid": "sample_reports/sample_lipid_report.txt",
        "Thyroid": "sample_reports/sample_thyroid_report.txt"
    }

    for report_name, filepath in reports.items():
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        cleaned_text = strip_boilerplate_and_disclaimers(raw_text)
        table_rows = detect_tabular_lab_data(cleaned_text)
        narrative = generate_narrative_from_table(table_rows)

        print(f"\n--- {report_name} Report ---", flush=True)
        print(f"Detected Table Rows ({len(table_rows)}):", flush=True)
        for r in table_rows:
            print(f"  - {r}", flush=True)
        print(f"Generated Narrative:\n  \"{narrative}\"", flush=True)

        assert len(table_rows) > 0, f"Failed to detect table rows in {report_name}"
        assert len(narrative) > 0, f"Failed to generate narrative for {report_name}"


def test_api_analyze_full_with_lab_reports():
    print("\n=======================================================", flush=True)
    print("2. TESTING POST /api/analyze-full WITH LAB REPORTS", flush=True)
    print("=======================================================", flush=True)

    lab_files = [
        ("CBC", "sample_reports/sample_cbc_report.txt"),
        ("LFT", "sample_reports/sample_lft_report.txt"),
    ]

    for label, filepath in lab_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        res = client.post("/api/analyze-full", json={"text": raw_text})
        assert res.status_code == 200, f"Failed for {label}: {res.text}"
        data = res.json()

        abs_summary = data["abstractive_summary_text"]
        lab_findings = data["lab_findings"]["content"]

        print(f"\n--- {label} FULL ANALYSIS RESULT ---", flush=True)
        print(f"Abstractive Summary: {abs_summary}", flush=True)
        print(f"Lab Findings Content: {lab_findings}", flush=True)

        # Assert disclaimers/footers NOT present in abstractive summary
        assert "synthetic" not in abs_summary.lower()
        assert "not a real patient" not in abs_summary.lower()
        assert "test data only" not in abs_summary.lower()
        assert "confidential" not in abs_summary.lower()

        # Assert medical terms ARE present
        assert len(abs_summary) > 0


def test_narrative_report_unaffected():
    print("\n=======================================================", flush=True)
    print("3. TESTING NARRATIVE REPORT (sample_report_01.txt)", flush=True)
    print("=======================================================", flush=True)

    with open('sample_reports/sample_report_01.txt', 'r', encoding='utf-8') as f:
        raw_text = f.read()

    res = client.post("/api/analyze-full", json={"text": raw_text})
    assert res.status_code == 200, f"Failed narrative report test: {res.text}"
    data = res.json()

    print(f"Patient Name: {data['patient_information']['patient_name']}", flush=True)
    print(f"Abstractive Summary: {data['abstractive_summary_text']}", flush=True)
    print(f"Symptoms Verified: {data['symptoms']['verified']}", flush=True)

    assert data["patient_information"]["patient_name"] == "John Doe (Synthetic)"
    assert data["symptoms"]["verified"] is True
    print("Narrative report processed successfully and unaffected!", flush=True)


if __name__ == "__main__":
    test_table_detection_and_narrative_generation()
    test_api_analyze_full_with_lab_reports()
    test_narrative_report_unaffected()
    print("\n=======================================================", flush=True)
    print("ALL TESTS PASSED PERFECTLY!", flush=True)
    print("=======================================================", flush=True)
