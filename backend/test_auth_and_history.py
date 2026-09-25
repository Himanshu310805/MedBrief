import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_and_report_isolation():
    print("=== TESTING AUTHENTICATION & PER-USER REPORT ISOLATION ===")

    timestamp = int(time.time())
    email1 = f"doctor_{timestamp}_1@example.com"
    email2 = f"doctor_{timestamp}_2@example.com"
    password = "SecurePassword123!"

    # 1. Unauthenticated Request Rejection Test
    res_no_auth = client.post("/api/extract-text", json={"text": "Patient has hypertension."})
    assert res_no_auth.status_code == 401, f"Expected 401 for unauthenticated request, got {res_no_auth.status_code}"
    print("PASS: Unauthenticated endpoint request rejected with HTTP 401.")

    # 2. Signup User 1
    res_signup1 = client.post("/api/auth/signup", json={"email": email1, "password": password})
    assert res_signup1.status_code == 201, f"Signup failed: {res_signup1.text}"
    data1 = res_signup1.json()
    token1 = data1["access_token"]
    user1_id = data1["user"]["id"]
    print(f"PASS: User 1 signed up successfully (ID: {user1_id}, Email: {email1}). Token generated.")

    # 3. Duplicate Email Rejection Test
    res_dup = client.post("/api/auth/signup", json={"email": email1, "password": password})
    assert res_dup.status_code == 400, f"Expected 400 for duplicate email, got {res_dup.status_code}"
    print("PASS: Duplicate email signup rejected with HTTP 400.")

    # 4. Login User 1 (Wrong & Correct Password)
    res_wrong_login = client.post("/api/auth/login", json={"email": email1, "password": "WrongPassword"})
    assert res_wrong_login.status_code == 401
    print("PASS: Login with wrong password rejected with HTTP 401.")

    res_login1 = client.post("/api/auth/login", json={"email": email1, "password": password})
    assert res_login1.status_code == 200
    assert res_login1.json()["access_token"]
    print("PASS: Login with correct password succeeded.")

    # 5. GET /api/auth/me Test
    headers1 = {"Authorization": f"Bearer {token1}"}
    res_me = client.get("/api/auth/me", headers=headers1)
    assert res_me.status_code == 200
    assert res_me.json()["user"]["email"] == email1
    print("PASS: GET /api/auth/me returned correct user profile.")

    # 6. Signup User 2
    res_signup2 = client.post("/api/auth/signup", json={"email": email2, "password": password})
    assert res_signup2.status_code == 201
    token2 = res_signup2.json()["access_token"]
    user2_id = res_signup2.json()["user"]["id"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    print(f"PASS: User 2 signed up successfully (ID: {user2_id}, Email: {email2}).")

    # 7. Analyze Reports for User 1 and User 2
    sample_text_1 = "PATIENT: John Doe. DIAGNOSIS: Essential hypertension."
    res_ana1 = client.post("/api/analyze-full", json={"text": sample_text_1}, headers=headers1)
    assert res_ana1.status_code == 200

    sample_text_2 = "PATIENT: Jane Smith. DIAGNOSIS: Acute bronchitis."
    res_ana2 = client.post("/api/analyze-full", json={"text": sample_text_2}, headers=headers2)
    assert res_ana2.status_code == 200

    # 8. Report History Isolation Check
    res_rep1 = client.get("/api/reports", headers=headers1)
    assert res_rep1.status_code == 200
    reports1 = res_rep1.json()["reports"]
    assert len(reports1) == 1
    report1_id = reports1[0]["id"]
    assert reports1[0]["user_id"] == user1_id
    print(f"PASS: User 1 sees ONLY their own report (Report ID: {report1_id}).")

    res_rep2 = client.get("/api/reports", headers=headers2)
    assert res_rep2.status_code == 200
    reports2 = res_rep2.json()["reports"]
    assert len(reports2) == 1
    report2_id = reports2[0]["id"]
    assert reports2[0]["user_id"] == user2_id
    print(f"PASS: User 2 sees ONLY their own report (Report ID: {report2_id}).")

    # 9. Cross-User Unauthorized Access Test (HTTP 403 Forbidden)
    res_cross = client.get(f"/api/reports/{report1_id}", headers=headers2)
    assert res_cross.status_code == 403, f"Expected 403 for cross-user report access, got {res_cross.status_code}"
    print("PASS: Accessing another user's report returned HTTP 403 Forbidden.")

    res_own = client.get(f"/api/reports/{report1_id}", headers=headers1)
    assert res_own.status_code == 200
    print("PASS: Accessing own report returned HTTP 200 OK.")

    print("\nALL AUTHENTICATION & REPORT ISOLATION TESTS PASSED 100% PERFECTLY!")

if __name__ == '__main__':
    test_auth_and_report_isolation()
