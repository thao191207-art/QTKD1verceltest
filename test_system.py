import os
import json
import io
from server import app

def run_tests():
    client = app.test_client()
    print(">>> 1. Testing GET / (Dashboard UI)...")
    res = client.get('/')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "ĐẠI THÀNH APPLIANCES" in res.get_data(as_text=True)
    print("    PASSED!")

    print(">>> 2. Testing GET /api/statistics...")
    res = client.get('/api/statistics')
    assert res.status_code == 200
    data = res.get_json()
    assert "total_dossiers" in data
    assert "tier_counts" in data
    print(f"    PASSED! Total dossiers: {data['total_dossiers']}, Phantom traps: {data['phantom_count']}")

    print(">>> 3. Testing GET /api/dossiers...")
    res = client.get('/api/dossiers')
    assert res.status_code == 200
    dossiers = res.get_json()
    assert len(dossiers) >= 3
    print(f"    PASSED! Loaded {len(dossiers)} dossiers.")

    first_id = dossiers[0]["id"]
    print(f">>> 4. Testing GET /api/dossiers/{first_id}...")
    res = client.get(f'/api/dossiers/{first_id}')
    assert res.status_code == 200
    d_detail = res.get_json()
    assert d_detail["id"] == first_id
    assert "partner_profile" in d_detail
    assert "compliance_report" in d_detail
    assert "verification_tickets" in d_detail
    assert "scoring_result" in d_detail
    assert "executive_assessment" in d_detail
    assert "final_dossier" in d_detail
    print("    PASSED! Complete 6-step data present.")

    print(">>> 5. Testing POST /api/intake/form (New Partner Intake)...")
    new_partner_form = {
        "legal": {
            "company_name": "Công ty TNHH Cơ Điện Lạnh Thăng Long",
            "tax_id": "0109988776",
            "representative": "Bùi Tuấn Hưng",
            "phone": "0988776655",
            "email": "thanglong.cold@gmail.com",
            "established_year": 2019,
            "region": "KV1"
        },
        "location": {
            "address": "Số 99 Lê Đức Thọ, Phường Mỹ Đình, Quận Nam Từ Liêm, Hà Nội",
            "city": "Hà Nội",
            "district": "Quận Nam Từ Liêm",
            "lat": 21.0285,
            "lng": 105.7701
        },
        "commercial": {
            "monthly_commitment_millions": 1600,
            "main_categories": ["Bếp từ", "Máy lọc nước", "Bình nóng lạnh"],
            "target_tier": "Đại lý Cấp 1",
            "experience_years": 5
        },
        "warranty": {
            "technician_count": 3,
            "service_area_sqm": 30,
            "sla_hours": 24,
            "transport_vehicles": 2,
            "can_repair_on_site": True
        },
        "finance": {
            "credit_limit_millions": 600,
            "credit_days": 30,
            "has_bank_guarantee": True,
            "bank_guarantee_amount_millions": 600,
            "desired_discount_percent": 22.0
        }
    }
    res = client.post('/api/intake/form', json=new_partner_form)
    assert res.status_code == 201
    created_dossier = res.get_json()["dossier"]
    created_id = created_dossier["id"]
    print(f"    PASSED! Created dossier {created_id} (Score: {created_dossier['scoring_result']['total_score']}, Tier: {created_dossier['scoring_result']['tier']})")

    print(">>> 6. Testing POST /api/intake/file with DOCX upload...")
    sample_docx = os.path.join(os.path.dirname(__file__), "data", "sample_files", "ho_so_dai_ly_chuan_vang.docx")
    with open(sample_docx, "rb") as f:
        file_bytes = f.read()
    res = client.post('/api/intake/file', data={
        'file': (io.BytesIO(file_bytes), 'ho_so_dai_ly_chuan_vang.docx')
    }, content_type='multipart/form-data')
    assert res.status_code == 201
    file_dossier = res.get_json()["dossier"]
    print(f"    PASSED! DOCX Extracted: {file_dossier['partner_profile']['legal']['company_name']} (ID: {file_dossier['id']})")

    print(">>> 7. Testing POST /api/intake/file with PDF upload...")
    sample_pdf = os.path.join(os.path.dirname(__file__), "data", "sample_files", "ho_so_bay_cam_ket_ao.pdf")
    with open(sample_pdf, "rb") as f:
        pdf_bytes = f.read()
    res = client.post('/api/intake/file', data={
        'file': (io.BytesIO(pdf_bytes), 'ho_so_bay_cam_ket_ao.pdf')
    }, content_type='multipart/form-data')
    assert res.status_code == 201
    pdf_dossier = res.get_json()["dossier"]
    assert pdf_dossier["scoring_result"]["is_phantom_commitment"] == True
    print(f"    PASSED! PDF Extracted: {pdf_dossier['partner_profile']['legal']['company_name']} (Phantom trap successfully caught! Score: {pdf_dossier['scoring_result']['total_score']})")

    print(f">>> 8. Testing Step 3 Verification Update on {created_id}...")
    updates = {
        "service": {
            "actual_technician_count": 4,
            "actual_service_area_sqm": 35,
            "sla_commitment_verified": True,
            "service_notes": "Kiểm tra thực tế xưởng khang trang, đầy đủ 4 kỹ sư."
        }
    }
    res = client.post(f'/api/dossiers/{created_id}/verify', json=updates)
    assert res.status_code == 200
    updated_d = res.get_json()["dossier"]
    assert updated_d["verification_tickets"]["service"]["actual_technician_count"] == 4
    print("    PASSED! Re-scoring after verification completed.")

    print(f">>> 9. Testing Step 5 Human-in-the-Loop Cockpit Decision on {created_id}...")
    decision_payload = {
        "decision": "TIẾP TỤC",
        "notes": "Hồ sơ đạt tiêu chuẩn chất lượng cao. Duyệt tiến hành ký kết hợp đồng phân phối."
    }
    res = client.post(f'/api/dossiers/{created_id}/decision', json=decision_payload)
    assert res.status_code == 200
    dec_dossier = res.get_json()["dossier"]
    assert dec_dossier["status"] == "APPROVED"
    assert dec_dossier["executive_assessment"]["manager_decision"] == "TIẾP TỤC"
    assert dec_dossier["final_dossier"]["is_finalized"] == True
    assert len(dec_dossier["final_dossier"]["conditions_precedent"]) > 0
    assert "ĐẠI THÀNH" in dec_dossier["final_dossier"]["response_letter"]["subject"]
    print("    PASSED! Decision recorded, Conditions Precedent and Letter drafted.")

    print(">>> 10. Testing Excel Export (/api/export/excel)...")
    res = client.get('/api/export/excel')
    assert res.status_code == 200
    assert len(res.data) > 1000
    print(f"    PASSED! Excel exported successfully ({len(res.data)} bytes).")

    print(">>> 11. Testing Existing Partners & Policies...")
    res = client.get('/api/partners')
    assert res.status_code == 200
    partners = res.get_json()
    assert len(partners) >= 8
    res = client.get('/api/policies')
    assert res.status_code == 200
    print("    PASSED! Reference databases accessible.")

    print(">>> 12. Testing Sample files download...")
    res = client.get('/api/samples')
    assert res.status_code == 200
    samples = res.get_json()
    assert len(samples) >= 6
    print(f"    PASSED! {len(samples)} sample files ready.")

    print("\n=======================================================")
    print(" ALL 12 INTEGRATION & WORKFLOW TESTS PASSED 100%!")
    print("=======================================================")

if __name__ == '__main__':
    run_tests()

