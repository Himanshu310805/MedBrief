import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_name_and_history_feature():
    print("=== TESTING FULL NAME SIGNUP & REPORT HISTORY FEATURE ===")

    timestamp = int(time.time())
    email = f"dr_sarah_{timestamp}@example.com"
    full_name = "Dr. Sarah Connor"
    password = "SecurePassword123!"

    # 1. Signup with Full Name
    res_signup = client.post("/api/auth/signup", json={
        "full_name": full_name,
        "email": email,
        "password": password
    })
    assert res_signup.status_code == 201, f"Signup failed: {res_signup.text}"
    user_data = res_signup.json()["user"]
    token = res_signup.json()["access_token"]

    assert user_data["full_name"] == full_name, f"Expected full_name '{full_name}', got '{user_data.get('full_name')}'"
    print(f"PASS 1: Signup created user with Full Name '{user_data['full_name']}' and email '{user_data['email']}'.")

    # 2. GET /api/auth/me Profile Check
    headers = {"Authorization": f"Bearer {token}"}
    res_me = client.get("/api/auth/me", headers=headers)
    assert res_me.status_code == 200
    me_data = res_me.json()["user"]
    assert me_data["full_name"] == full_name
    print(f"PASS 2: GET /api/auth/me returned Full Name '{me_data['full_name']}'.")

    # 3. Analyze Report and Save History
    sample_report = (
        "Patient Name: Mrs. Clara Oswald\n"
        "Age: 34 | Gender: Female\n"
        "CHIEF COMPLAINT: Patient reports mild cough and low-grade fever. "
        "DIAGNOSIS: Acute bronchitis. "
        "TREATMENT PLAN: Amoxicillin 500mg daily. Follow-up in 1 week."
    )
    res_analyze = client.post("/api/analyze-full", json={"text": sample_report}, headers=headers)
    assert res_analyze.status_code == 200
    print("PASS 3: Report analyzed and saved to user report history.")

    # 4. GET /api/reports History Check
    res_history = client.get("/api/reports", headers=headers)
    assert res_history.status_code == 200
    history_data = res_history.json()
    assert history_data["count"] >= 1
    first_report = history_data["reports"][0]
    assert first_report["patient_name"] == "Mrs. Clara Oswald"
    assert first_report["structured_summary"] is not None
    print(f"PASS 4: GET /api/reports returned {history_data['count']} saved report(s). Patient: {first_report['patient_name']}.")

    print("\nALL FULL NAME & REPORT HISTORY TESTS PASSED 100% PERFECTLY!")

if __name__ == '__main__':
    test_full_name_and_history_feature()
