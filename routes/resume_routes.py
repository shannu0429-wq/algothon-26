import os
import uuid
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models import db, Resume, User
from routes.auth_routes import login_required
from services.document_parser import extract_document_text
from services.resume_parser import parse_resume_content
from services.skill_extractor import extract_skills

resume_bp = Blueprint("resume", __name__)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

@resume_bp.route("/resume")
@login_required
def view_resume():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()

    parsed = latest_resume.get_parsed_data() if latest_resume else None
    return render_template("resume.html", user=user, resume=latest_resume, parsed=parsed)

@resume_bp.route("/resume/upload")
@resume_bp.route("/upload-resume", endpoint="upload_resume_view")
@login_required
def upload_page():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    return render_template("upload_resume.html", user=user)

@resume_bp.route("/api/resume/upload", methods=["POST"])
@login_required
def api_upload_resume():
    if "resume_file" not in request.files:
        return jsonify({"success": False, "error": "no file uploaded. please select a resume."}), 400

    file = request.files["resume_file"]
    if not file or file.filename == "":
        return jsonify({"success": False, "error": "empty file submitted. please select a valid file."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": "unsupported file format. please upload pdf, docx, txt, png, jpg, or jpeg."
        }), 400

    orig_name = secure_filename(file.filename).lower()
    ext = orig_name.rsplit(".", 1)[-1]
    unique_filename = f"{uuid.uuid4().hex[:12]}_{orig_name}"
    
    upload_dir = current_app.config["RESUME_UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, unique_filename)
    file.save(save_path)

    extracted_text, error_msg = extract_document_text(save_path)
    if error_msg or not extracted_text.strip():
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except Exception:
                pass
        return jsonify({
            "success": False,
            "error": error_msg or "could not extract readable text from the uploaded document."
        }), 422

    parsed_data = parse_resume_content(extracted_text)

    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    if user:
        p_info = parsed_data.get("personal_info", {})
        if p_info.get("name") and (not user.name or user.name == "new user"):
            user.name = p_info["name"].lower()
        if p_info.get("location") and not user.location:
            user.location = p_info["location"].lower()
        if p_info.get("linkedin") and not user.linkedin:
            user.linkedin = p_info["linkedin"].lower()
        if p_info.get("github") and not user.github:
            user.github = p_info["github"].lower()
        if p_info.get("portfolio") and not user.portfolio:
            user.portfolio = p_info["portfolio"].lower()

    new_resume = Resume(
        user_id=user_id,
        filename=orig_name,
        extracted_text=extracted_text
    )
    new_resume.set_parsed_data(parsed_data)
    db.session.add(new_resume)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "resume uploaded and analyzed successfully.",
        "resume_id": new_resume.id,
        "parsed_data": parsed_data,
        "redirect_url": url_for("resume.view_resume")
    })

@resume_bp.route("/api/resume/<int:resume_id>", methods=["GET"])
@login_required
def api_get_resume(resume_id):
    user_id = session.get("user_id")
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
    if not resume:
        return jsonify({"success": False, "error": "resume not found."}), 404
    return jsonify({"success": True, "resume": resume.to_dict()})

@resume_bp.route("/api/resume/update", methods=["POST"])
@login_required
def api_update_resume():
    user_id = session.get("user_id")
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    if not latest_resume:
        return jsonify({"success": False, "error": "no active resume to update."}), 404

    payload = request.get_json() or {}
    current_data = latest_resume.get_parsed_data()

    if "name" in payload:
        current_data.setdefault("personal_info", {})["name"] = payload["name"].strip().lower()
    if "email" in payload:
        current_data.setdefault("personal_info", {})["email"] = payload["email"].strip().lower()
    if "phone" in payload:
        current_data.setdefault("personal_info", {})["phone"] = payload["phone"].strip().lower()
    if "location" in payload:
        current_data.setdefault("personal_info", {})["location"] = payload["location"].strip().lower()
    if "summary" in payload:
        current_data["summary"] = payload["summary"].strip().lower()
    if "skills" in payload:
        skill_list = [s.strip().lower() for s in payload["skills"] if s.strip()]
        current_data["skills"] = skill_list
        re_extracted = extract_skills(" ".join(skill_list))
        current_data["skills_by_category"] = re_extracted["skills_by_category"]

    latest_resume.set_parsed_data(current_data)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "candidate profile updated successfully.",
        "parsed_data": current_data
    })
