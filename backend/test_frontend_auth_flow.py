import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

USER_IMG1 = r"C:\Users\himan\.gemini\antigravity\brain\264afcd6-30ee-4a99-99ce-b075f9684189\.user_uploaded\media_1790186784527.jpg"

def test_frontend_auth_flow():
    print("=== TESTING COMPLETE FRONTEND & BACKEND AUTH FLOW ===")

    # 1. Unauthenticated Request -> Expect 401
    res = client.post("/api/extract-text", json={"text": "Test report"})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}"
    print("PASS 1: Unauthenticated request rejected with HTTP 401 (matches user error log).")

    # 2. Signup User
    email = f"user_{int(time.time())}@example.com"
    res_signup = client.post("/api/auth/signup", json={"email": email, "password": "Password123!"})
    assert res_signup.status_code == 201, f"Signup failed: {res_signup.text}"
    token = res_signup.json()["access_token"]
    print(f"PASS 2: Signup created account '{email}' and generated JWT access token.")

    # 3. Authenticated Extract Image -> Expect 200 OK
    headers = {"Authorization": f"Bearer {token}"}
    with open(USER_IMG1, 'rb') as f:
        res_extract = client.post("/api/extract-image", files={'file': ('varad.jpg', f, 'image/jpeg')}, headers=headers)
    assert res_extract.status_code == 200, f"Extraction failed: {res_extract.text}"
    raw_text = res_extract.json()["extracted_text"]
    print("PASS 3: Authenticated image OCR extraction succeeded.")

    # 4. Authenticated Analyze Full -> Expect 200 OK
    res_analyze = client.post("/api/analyze-full", json={"text": raw_text}, headers=headers)
    assert res_analyze.status_code == 200, f"Analysis failed: {res_analyze.text}"
    data = res_analyze.json()
    assert len(data["lab_results_table"]) >= 10
    print(f"PASS 4: Authenticated full analysis succeeded ({len(data['lab_results_table'])} lab rows).")

    # 5. Authenticated Download PDF -> Expect 200 OK
    res_pdf = client.post("/api/download-report", json=data, headers=headers)
    assert res_pdf.status_code == 200, f"Download failed: {res_pdf.text}"
    assert res_pdf.content.startswith(b"%PDF-")
    print("PASS 5: Authenticated PDF download succeeded.")

    print("\nALL FRONTEND AUTH & API INTEGRATION TESTS PASSED PERFECTLY!")

if __name__ == '__main__':
    test_frontend_auth_flow()
