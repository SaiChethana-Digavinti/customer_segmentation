# ============================================================
# ANALYSIS HISTORY AUTOMATED TEST SUITE
# CUSTOMER SEGMENTATION & AI MARKETING
# ============================================================

import json
from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import SessionLocal
from app.database.models import User, AnalysisHistory, AuditLog
from app.services.history_service import seed_default_history

client = TestClient(app)


def test_database_and_seeding():
    """Verify analysis_history table exists and is seeded."""
    db = SessionLocal()
    try:
        seed_default_history(db)
        count = db.query(AnalysisHistory).count()
        assert count > 0, "Expected seeded analysis history records"
        print(f"✅ DB Seeding verified: {count} historical records in database.")
    finally:
        db.close()


def test_role_based_access_and_scoping():
    """Verify Admin sees all records, while Analyst sees only their own."""
    # 1. Login as Admin
    admin_login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Login as Analyst
    analyst_login = client.post("/auth/login", json={"username": "analyst", "password": "user123"})
    assert analyst_login.status_code == 200, f"Analyst login failed: {analyst_login.text}"
    analyst_token = analyst_login.json()["access_token"]
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}

    # Admin fetches history
    admin_res = client.get("/history", headers=admin_headers)
    assert admin_res.status_code == 200
    admin_data = admin_res.json()
    admin_records = admin_data["records"]
    admin_total = admin_data["total"]

    # Analyst fetches history
    analyst_res = client.get("/history", headers=analyst_headers)
    assert analyst_res.status_code == 200
    analyst_data = analyst_res.json()
    analyst_records = analyst_data["records"]
    analyst_total = analyst_data["total"]

    print(f"✅ Admin sees {admin_total} records; Analyst sees {analyst_total} records.")
    assert admin_total >= analyst_total, "Admin should see at least as many records as Analyst"

    # Verify Analyst records only belong to analyst
    db = SessionLocal()
    try:
        analyst_user = db.query(User).filter(User.username == "analyst").first()
        for r in analyst_records:
            assert r["user_id"] == analyst_user.id or r["user_id"] is None
    finally:
        db.close()


def test_security_unauthorized_access():
    """Verify Analyst cannot view or delete Admin-owned records."""
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        admin_record = db.query(AnalysisHistory).filter(AnalysisHistory.user_id == admin_user.id).first()
        assert admin_record is not None, "Need at least one admin-owned record to test security"
        admin_rec_id = admin_record.id
    finally:
        db.close()

    # Login as Analyst
    analyst_login = client.post("/auth/login", json={"username": "analyst", "password": "user123"})
    analyst_token = analyst_login.json()["access_token"]
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"}

    # Attempt to view Admin record as Analyst -> Expect 403
    view_res = client.get(f"/history/{admin_rec_id}", headers=analyst_headers)
    assert view_res.status_code == 403, f"Expected 403 Forbidden, got {view_res.status_code}"
    print("✅ Security passed: Analyst blocked from viewing Admin record (HTTP 403).")

    # Attempt to delete Admin record as Analyst -> Expect 403
    delete_res = client.delete(f"/history/{admin_rec_id}", headers=analyst_headers)
    assert delete_res.status_code == 403, f"Expected 403 Forbidden, got {delete_res.status_code}"
    print("✅ Security passed: Analyst blocked from deleting Admin record (HTTP 403).")

    # Attempt to export Admin record as Analyst -> Expect 403
    export_res = client.get(f"/history/{admin_rec_id}/export/csv", headers=analyst_headers)
    assert export_res.status_code == 403, f"Expected 403 Forbidden, got {export_res.status_code}"
    print("✅ Security passed: Analyst blocked from exporting Admin record (HTTP 403).")


def test_search_and_filters():
    """Verify search by ID/Name, segment filter, and recommendation keyword filter."""
    admin_login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    # 1. Search by customer ID "1007"
    res1 = client.get("/history?search=1007", headers=admin_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] >= 1
    assert any("1007" in r["customer_id"] for r in data1["records"])
    print("✅ Search by Customer ID verified.")

    # 2. Filter by Segment "Champions"
    res2 = client.get("/history?segment=Champions", headers=admin_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total"] >= 1
    for r in data2["records"]:
        assert r["predicted_segment"] == "Champions"
    print("✅ Filter by Segment verified.")

    # 3. Filter by Recommendation keyword "VIP"
    res3 = client.get("/history?recommendation_type=VIP", headers=admin_headers)
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["total"] >= 1
    print("✅ Filter by Recommendation Keyword verified.")


def test_view_record_details():
    """Verify GET /history/{id} returns saved details without re-generating AI."""
    admin_login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    res = client.get("/history", headers=admin_headers)
    record_id = res.json()["records"][0]["id"]

    detail_res = client.get(f"/history/{record_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()

    assert detail["id"] == record_id
    assert "customer_id" in detail
    assert "segmentation_data" in detail
    assert "recency" in detail["segmentation_data"]
    assert "monetary" in detail["segmentation_data"]
    assert "predicted_segment" in detail
    assert "ai_recommendation" in detail
    assert len(detail["ai_recommendation"]) > 0
    print(f"✅ View analysis details verified for ID #{record_id}.")


def test_historical_report_downloads():
    """Verify historical reports in all 5 formats: CSV, XLSX, PDF, DOCX, JSON."""
    admin_login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    res = client.get("/history", headers=admin_headers)
    record_id = res.json()["records"][0]["id"]

    # 1. CSV
    csv_res = client.get(f"/history/{record_id}/export/csv", headers=admin_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert len(csv_res.text) > 20
    print("✅ Historical CSV export verified.")

    # 2. XLSX
    xlsx_res = client.get(f"/history/{record_id}/export/xlsx", headers=admin_headers)
    assert xls_res.status_code == 200 if 'xls_res' in locals() else xlsx_res.status_code == 200
    assert "openxmlformats-officedocument.spreadsheetml" in xlsx_res.headers["content-type"]
    assert len(xlsx_res.content) > 1000
    print("✅ Historical XLSX export verified.")

    # 3. PDF
    pdf_res = client.get(f"/history/{record_id}/export/pdf", headers=admin_headers)
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers["content-type"]
    assert pdf_res.content.startswith(b"%PDF")
    print("✅ Historical PDF export verified.")

    # 4. DOCX
    docx_res = client.get(f"/history/{record_id}/export/docx", headers=admin_headers)
    assert docx_res.status_code == 200
    assert "openxmlformats-officedocument.wordprocessingml" in docx_res.headers["content-type"]
    assert docx_res.content.startswith(b"PK\x03\x04")
    print("✅ Historical DOCX export verified.")

    # 5. JSON
    json_res = client.get(f"/history/{record_id}/export/json", headers=admin_headers)
    assert json_res.status_code == 200
    assert "application/json" in json_res.headers["content-type"]
    payload = json.loads(json_res.text)
    assert "customer_id" in payload
    assert "ai_recommendation" in payload
    print("✅ Historical JSON export verified.")


def test_auto_save_on_ai_recommendation():
    """Verify GET /{customer_id}/ai-recommendation auto-saves into AnalysisHistory."""
    analyst_login = client.post("/auth/login", json={"username": "analyst", "password": "user123"})
    analyst_headers = {"Authorization": f"Bearer {analyst_login.json()['access_token']}"}

    # Generate recommendation for customer 1003
    ai_res = client.get("/customers/1003/ai-recommendation", headers=analyst_headers)
    assert ai_res.status_code == 200
    ai_data = ai_res.json()
    assert "ai_message" in ai_data

    # Check that it automatically appears in history
    hist_res = client.get("/history?search=1003", headers=analyst_headers)
    assert hist_res.status_code == 200
    records = hist_res.json()["records"]
    assert len(records) >= 1
    assert any("1003" in r["customer_id"] for r in records)
    print("✅ Automatic history logging on AI recommendation verified.")


def test_delete_with_audit_log():
    """Verify record deletion and security audit logging."""
    analyst_login = client.post("/auth/login", json={"username": "analyst", "password": "user123"})
    analyst_headers = {"Authorization": f"Bearer {analyst_login.json()['access_token']}"}

    # Create a fresh record for analyst
    db = SessionLocal()
    try:
        analyst = db.query(User).filter(User.username == "analyst").first()
        test_rec = AnalysisHistory(
            user_id=analyst.id,
            customer_id="9999",
            customer_name="Temporary Customer",
            predicted_segment="Champions",
            ai_recommendation="Test recommendation for deletion.",
            report_status="COMPLETED",
        )
        db.add(test_rec)
        db.commit()
        db.refresh(test_rec)
        target_id = test_rec.id
    finally:
        db.close()

    # Delete record
    del_res = client.delete(f"/history/{target_id}", headers=analyst_headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify deleted from DB
    db = SessionLocal()
    try:
        found = db.query(AnalysisHistory).filter(AnalysisHistory.id == target_id).first()
        assert found is None, "Record should be removed from database"

        # Verify audit log
        audit = db.query(AuditLog).filter(
            AuditLog.action == "DELETE_ANALYSIS_HISTORY",
            AuditLog.details.contains(str(target_id))
        ).first()
        assert audit is not None, "Expected audit log entry for delete operation"
        print(f"✅ Delete and audit logging verified for record #{target_id}.")
    finally:
        db.close()


def test_pagination():
    """Verify pagination limits and offset calculations."""
    admin_login = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    res = client.get("/history?page=1&page_size=2", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["records"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] >= 1
    print(f"✅ Pagination verified (total: {data['total']}, pages: {data['total_pages']}).")


if __name__ == "__main__":
    test_database_and_seeding()
    test_role_based_access_and_scoping()
    test_security_unauthorized_access()
    test_search_and_filters()
    test_view_record_details()
    test_historical_report_downloads()
    test_auto_save_on_ai_recommendation()
    test_delete_with_audit_log()
    test_pagination()
    print("\n🎉 ALL ANALYSIS HISTORY TESTS PASSED SUCCESSFULLY!")
