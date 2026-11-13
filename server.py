import os
import sys
import json
import datetime
from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename

from agent.pipeline_manager import pipeline_manager
from agent.extractor import extractor
from agent.dossier_generator import dossier_generator
from agent.llm_client import llm_client, load_config, save_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "data", "sample_files")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    stats = pipeline_manager.get_statistics()
    return jsonify(stats)


@app.route('/api/dossiers', methods=['GET'])
def list_dossiers():
    dossiers = pipeline_manager.load_dossiers()
    summaries = []
    for d in dossiers:
        profile = d.get("partner_profile", {})
        score = d.get("scoring_result", {})
        assess = d.get("executive_assessment", {})
        compliance = d.get("compliance_report", {})

        summaries.append({
            "id": d.get("id"),
            "created_at": d.get("created_at"),
            "status": d.get("status"),
            "current_step": d.get("current_step"),
            "company_name": profile.get("legal", {}).get("company_name"),
            "representative": profile.get("legal", {}).get("representative"),
            "region": profile.get("legal", {}).get("region"),
            "monthly_commitment": profile.get("commercial", {}).get("monthly_commitment_millions"),
            "total_score": score.get("total_score"),
            "tier": score.get("tier"),
            "tier_color": score.get("tier_color", "blue"),
            "is_phantom": score.get("is_phantom_commitment", False),
            "compliance_status": compliance.get("status", "PASS"),
            "compliance_flags": compliance.get("flags", []),
            "manager_decision": assess.get("manager_decision")
        })
    return jsonify(summaries)


@app.route('/api/dossiers/<dossier_id>', methods=['GET'])
def get_dossier_detail(dossier_id):
    dossier = pipeline_manager.get_dossier(dossier_id)
    if not dossier:
        return jsonify({"error": "Không tìm thấy hồ sơ đối tác"}), 404
    return jsonify(dossier)


@app.route('/api/intake/form', methods=['POST'])
def intake_form():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "Dữ liệu gửi lên không hợp lệ"}), 400

    try:
        dossier = pipeline_manager.create_dossier(data, intake_mode="FORM")
        return jsonify({"success": True, "dossier": dossier}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/intake/file', methods=['POST'])
def intake_file():
    if 'file' not in request.files:
        return jsonify({"error": "Vui lòng chọn tệp tin tải lên (.pdf, .docx, .txt)"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Chưa chọn tệp tin"}), 400

    filename = secure_filename(file.filename)
    file_bytes = file.read()

    try:
        profile, raw_text = extractor.process_file_upload(file_bytes, filename)
        dossier = pipeline_manager.create_dossier(profile, intake_mode="FILE_UPLOAD", raw_text=raw_text)
        return jsonify({
            "success": True, 
            "dossier": dossier, 
            "extracted_text_preview": raw_text[:500] + ("..." if len(raw_text) > 500 else "")
        }), 201
    except Exception as e:
        return jsonify({"error": f"Lỗi bóc tách tài liệu: {str(e)}"}), 500


@app.route('/api/intake/text', methods=['POST'])
def intake_text():
    data = request.get_json(force=True)
    raw_text = data.get("text", "")
    if not raw_text or len(raw_text.strip()) < 10:
        return jsonify({"error": "Văn bản quá ngắn, vui lòng cung cấp thêm thông tin đại lý"}), 400

    try:
        profile = extractor.process_raw_input(raw_text)
        dossier = pipeline_manager.create_dossier(profile, intake_mode="TEXT_PASTE", raw_text=raw_text)
        return jsonify({"success": True, "dossier": dossier}), 201
    except Exception as e:
        return jsonify({"error": f"Lỗi xử lý văn bản: {str(e)}"}), 500


@app.route('/api/dossiers/<dossier_id>/verify', methods=['POST'])
def verify_dossier(dossier_id):
    ticket_updates = request.get_json(force=True)
    if not ticket_updates:
        return jsonify({"error": "Không có dữ liệu cập nhật khảo sát"}), 400

    updated_dossier = pipeline_manager.update_verification_tickets(dossier_id, ticket_updates)
    if not updated_dossier:
        return jsonify({"error": "Không tìm thấy hồ sơ cần cập nhật"}), 404

    return jsonify({"success": True, "dossier": updated_dossier})


@app.route('/api/dossiers/<dossier_id>/decision', methods=['POST'])
def submit_decision(dossier_id):
    data = request.get_json(force=True)
    decision = data.get("decision")  # "TIẾP TỤC", "BỔ SUNG ĐIỀU KIỆN", "CHƯA TIẾP TỤC"
    notes = data.get("notes", "")

    if decision not in ["TIẾP TỤC", "BỔ SUNG ĐIỀU KIỆN", "CHƯA TIẾP TỤC"]:
        return jsonify({"error": "Quyết định phê duyệt không hợp lệ"}), 400

    updated_dossier = pipeline_manager.submit_manager_decision(dossier_id, decision, notes)
    if not updated_dossier:
        return jsonify({"error": "Không tìm thấy hồ sơ để phê duyệt"}), 404

    return jsonify({"success": True, "dossier": updated_dossier})


@app.route('/api/dossiers/<dossier_id>', methods=['DELETE'])
def delete_dossier(dossier_id):
    success = pipeline_manager.delete_dossier(dossier_id)
    if not success:
        return jsonify({"error": "Không tìm thấy hồ sơ để xóa"}), 404
    return jsonify({"success": True, "message": "Đã xóa hồ sơ thành công"})


@app.route('/api/export/excel', methods=['GET'])
def export_all_excel():
    dossiers = pipeline_manager.load_dossiers()
    excel_bytes = dossier_generator.export_pipeline_to_excel(dossiers)
    filename = f"Danh_Sach_Dai_Ly_Dai_Thanh_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return Response(
        excel_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route('/api/export/excel/<dossier_id>', methods=['GET'])
def export_single_excel(dossier_id):
    dossier = pipeline_manager.get_dossier(dossier_id)
    if not dossier:
        return jsonify({"error": "Không tìm thấy hồ sơ"}), 404

    excel_bytes = dossier_generator.export_pipeline_to_excel([dossier])
    comp_name = dossier.get("partner_profile", {}).get("legal", {}).get("company_name", dossier_id)
    safe_name = "".join(c for c in comp_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    filename = f"Tham_Dinh_Dai_Ly_{safe_name}_{dossier_id}.xlsx"
    return Response(
        excel_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route('/api/samples', methods=['GET'])
def list_samples():
    if not os.path.exists(SAMPLE_DIR):
        return jsonify([])
    files = [f for f in os.listdir(SAMPLE_DIR) if os.path.isfile(os.path.join(SAMPLE_DIR, f))]
    results = []
    descriptions = {
        "ho_so_dai_ly_chuan_vang": "Mẫu 1: Đại lý Chuẩn Vàng (Tier A - Hợp tác ngay, đủ 4 thợ, có bảo lãnh Vietcombank)",
        "ho_so_bay_cam_ket_ao": "Mẫu 2: Bẫy Cam Kết Ảo (Doanh số cam kết 2.8 tỷ, 0 thợ KTV, nợ 60 ngày - Cảnh báo đỏ phạt 25đ)",
        "ho_so_xung_dot_dia_ban_va_no_xau": "Mẫu 3: Xung Đột Địa Bàn & Nợ Xấu (Trùng đại diện nợ xấu cũ 485tr, vị trí cách đại lý Cấp 1 1.2km)"
    }
    for f in sorted(files):
        ext = os.path.splitext(f)[1]
        base = os.path.splitext(f)[0]
        desc = descriptions.get(base, f"Tệp tin hồ sơ {ext}")
        results.append({
            "filename": f,
            "extension": ext,
            "description": desc,
            "download_url": f"/api/samples/{f}"
        })
    return jsonify(results)


@app.route('/api/samples/<filename>', methods=['GET'])
def download_sample(filename):
    file_path = os.path.join(SAMPLE_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "Tệp tin mẫu không tồn tại"}), 404
    return send_file(file_path, as_attachment=True)


@app.route('/api/config', methods=['GET'])
def get_config():
    cfg = load_config()
    api_key = cfg.get("GEMINI_API_KEY", "")
    masked_key = ""
    if api_key:
        if len(api_key) > 8:
            masked_key = api_key[:4] + "..." + api_key[-4:]
        else:
            masked_key = "***"
    return jsonify({
        "is_configured": bool(api_key and len(api_key.strip()) > 10),
        "masked_key": masked_key,
        "model_name": cfg.get("MODEL_NAME", "gemini-2.5-flash"),
        "company_name": cfg.get("COMPANY_NAME", "Công ty Cổ phần Thiết bị Gia dụng Đại Thành"),
        "system_name": cfg.get("SYSTEM_NAME", "Hệ thống AI Agent Lựa Chọn & Phát Triển Đối Tác Phân Phối")
    })


@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.get_json(force=True)
    cfg = load_config()

    new_key = data.get("gemini_api_key")
    if new_key is not None:
        cfg["GEMINI_API_KEY"] = new_key.strip()
    
    new_model = data.get("model_name")
    if new_model:
        cfg["MODEL_NAME"] = new_model.strip()

    if save_config(cfg):
        llm_client.reload_config()
        return jsonify({"success": True, "message": "Đã cập nhật cấu hình hệ thống thành công"})
    return jsonify({"error": "Không thể lưu cấu hình"}), 500


@app.route('/api/test-gemini', methods=['POST'])
def test_gemini():
    llm_client.reload_config()
    res = llm_client.test_connection()
    return jsonify(res)


@app.route('/api/partners', methods=['GET'])
def get_existing_partners():
    from agent.compliance_checker import load_existing_partners
    return jsonify(load_existing_partners())


@app.route('/api/policies', methods=['GET'])
def get_policies():
    from agent.compliance_checker import load_policies
    return jsonify(load_policies())


@app.route('/api/seed-presets', methods=['POST'])
def seed_presets():
    pipeline_manager.save_dossiers([])
    pipeline_manager.seed_preset_dossiers_if_empty()
    return jsonify({"success": True, "message": "Đã nạp lại 3 hồ sơ chuẩn kiểm thử thành công"})


def main():
    cfg = load_config()
    port = int(cfg.get("PORT", 5000))
    host = cfg.get("HOST", "0.0.0.0")

    # Seed demo presets if empty on start
    pipeline_manager.seed_preset_dossiers_if_empty()

    print("=" * 70)
    print(" HỆ THỐNG AI AGENT LỰA CHỌN & PHÁT TRIỂN ĐỐI TÁC PHÂN PHỐI")
    print(" CÔNG TY CỔ PHẦN THIẾT BỊ GIA DỤNG ĐẠI THÀNH")
    print(f" Web Server đang chạy tại: http://localhost:{port}")
    print("=" * 70)

    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()

