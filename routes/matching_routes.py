import os
import uuid
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from models import db, Resume, Job, Match, User, Skill
from routes.auth_routes import login_required
from services.document_parser import extract_document_text
from services.job_parser import parse_job_description
from services.matching_engine import match_resume_to_job
from services.resume_parser import parse_resume_content

matching_bp = Blueprint("matching", __name__)

@matching_bp.route("/job-matcher")
@login_required
def job_matcher_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    all_jobs_records = Job.query.order_by(Job.title.asc()).all()
    all_jobs = [j.to_dict() for j in all_jobs_records]

    target_job_id = request.args.get("job_id")
    prefill_job = None
    if target_job_id:
        prefill_job = db.session.get(Job, target_job_id)

    candidate_skills = []
    if latest_resume:
        candidate_skills = latest_resume.get_parsed_data().get("skills", [])

    return render_template(
        "job_matcher.html",
        user=user,
        resume=latest_resume,
        has_resume=latest_resume is not None,
        candidate_skills=candidate_skills[:12],
        total_skills_count=len(candidate_skills),
        all_jobs=all_jobs,
        sample_jobs=all_jobs[:5],
        prefill_job=prefill_job.to_dict() if prefill_job else None
    )

@matching_bp.route("/match-result/<int:match_id>")
@login_required
def match_result_view(match_id):
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    match = Match.query.filter_by(id=match_id, user_id=user_id).first_or_404()
    resume = db.session.get(Resume, match.resume_id)
    job = db.session.get(Job, match.job_id) if match.job_id else None

    from services.matching_engine import get_match_category
    category = get_match_category(match.overall_score)

    return render_template(
        "match_result.html",
        user=user,
        match=match.to_dict(),
        category=category,
        resume=resume.to_dict() if resume else None,
        job=job.to_dict() if job else None
    )

@matching_bp.route("/history")
@login_required
def history_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    matches = Match.query.filter_by(user_id=user_id).order_by(Match.created_at.desc()).all()
    return render_template("history.html", user=user, matches=[m.to_dict() for m in matches])

@matching_bp.route("/api/job/analyze", methods=["POST"])
@login_required
def api_analyze_job():
    job_text = request.form.get("job_description", "")
    title = request.form.get("title", "")
    company = request.form.get("company", "")
    location = request.form.get("location", "")

    if "job_file" in request.files:
        file = request.files["job_file"]
        if file and file.filename != "":
            orig_name = secure_filename(file.filename).lower()
            unique_name = f"{uuid.uuid4().hex[:12]}_{orig_name}"
            upload_dir = current_app.config["JOB_UPLOAD_FOLDER"]
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, unique_name)
            file.save(save_path)
            extracted, err = extract_document_text(save_path)
            if not err and extracted.strip():
                job_text = extracted

    if not job_text.strip():
        return jsonify({"success": False, "error": "please provide job description text or an uploaded file."}), 400

    parsed = parse_job_description(job_text, default_title=title, default_company=company, default_location=location)
    return jsonify({"success": True, "parsed_job": parsed})

@matching_bp.route("/api/match", methods=["POST"])
@login_required
def api_match():
    user_id = session.get("user_id")
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()

    if not latest_resume:
        return jsonify({"success": False, "error": "please upload a resume first before analyzing matches."}), 400

    parsed_resume = latest_resume.get_parsed_data()
    raw_resume_text = latest_resume.extracted_text

    data = request.form.to_dict() if request.form else (request.get_json() or {})
    job_id = data.get("job_id")
    job_record = None

    if job_id:
        job_record = db.session.get(Job, job_id)
        if job_record:
            job_data = {
                "title": job_record.title,
                "company": job_record.company,
                "location": job_record.location,
                "required_skills": job_record.get_required_skills(),
                "preferred_skills": job_record.get_preferred_skills(),
                "experience": job_record.experience_required,
                "education": job_record.education_required,
                "description": job_record.description
            }
            raw_job_text = job_record.description
    
    if not job_record:
        job_text = data.get("job_description", "")
        if "job_file" in request.files:
            file = request.files["job_file"]
            if file and file.filename != "":
                orig_name = secure_filename(file.filename).lower()
                unique_name = f"{uuid.uuid4().hex[:12]}_{orig_name}"
                upload_dir = current_app.config["JOB_UPLOAD_FOLDER"]
                os.makedirs(upload_dir, exist_ok=True)
                save_path = os.path.join(upload_dir, unique_name)
                file.save(save_path)
                extracted, err = extract_document_text(save_path)
                if not err and extracted.strip():
                    job_text = extracted

        if not job_text.strip():
            return jsonify({"success": False, "error": "please provide a job description or select an existing job."}), 400

        title = data.get("title", "")
        company = data.get("company", "")
        location = data.get("location", "")
        job_data = parse_job_description(job_text, default_title=title, default_company=company, default_location=location)
        raw_job_text = job_text

    match_result = match_resume_to_job(
        parsed_resume,
        job_data,
        raw_resume_text=raw_resume_text,
        raw_job_text=raw_job_text
    )

    new_match = Match(
        user_id=user_id,
        resume_id=latest_resume.id,
        job_id=job_record.id if job_record else None,
        job_title=job_data.get("title", "custom role"),
        company_name=job_data.get("company", "target company"),
        overall_score=match_result["overall_score"],
        skill_score=match_result["breakdown"]["skill_score"],
        experience_score=match_result["breakdown"]["experience_score"],
        semantic_score=match_result["breakdown"]["semantic_score"],
        education_score=match_result["breakdown"]["education_score"],
        project_score=match_result["breakdown"]["project_score"]
    )
    new_match.set_matched_skills(match_result["matched_skills"])
    new_match.set_missing_skills(match_result["missing_skills"])
    new_match.set_partial_skills(match_result["partial_skills"])
    new_match.set_explanation(match_result["explanation"])
    new_match.set_recommendations(match_result["recommendations"])

    db.session.add(new_match)
    db.session.commit()

    return jsonify({
        "success": True,
        "match_id": new_match.id,
        "redirect_url": url_for("matching.match_result_view", match_id=new_match.id),
        "result": match_result
    })

@matching_bp.route("/api/demo-match", methods=["POST"])
def api_demo_match():
    user_id = session.get("user_id")
    if not user_id:
        user = User.query.filter_by(email="demo@jobalign.ai").first()
        if not user:
            user = User(name="alex rivera", email="demo@jobalign.ai")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email
    else:
        user = db.session.get(User, user_id)

    sample_resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.uploaded_at.desc()).first()
    if not sample_resume:
        sample_resume_text = (
            "alex rivera\n"
            "alex.rivera@example.com | (555) 234-5678 | san francisco, ca\n"
            "professional summary\n"
            "results-driven software engineer with 3+ years of experience designing and deploying scalable backend systems, rest apis, and machine learning pipelines. proficient in python, flask, mysql, docker, and cloud environments.\n"
            "technical skills: python, flask, fastapi, mysql, postgresql, redis, docker, git, rest api, machine learning, deep learning, pytorch, scikit-learn, linux\n"
            "education: b.s. in computer science, uc berkeley, 2021\n"
            "experience: software engineer at novatech solutions (2022 - present). built python/flask microservices, optimized mysql queries, deployed with docker.\n"
            "projects: ai resume analyzer built with python and flask."
        )
        parsed = parse_resume_content(sample_resume_text)
        sample_resume = Resume(user_id=user.id, filename="demo_resume.txt", extracted_text=sample_resume_text)
        sample_resume.set_parsed_data(parsed)
        db.session.add(sample_resume)
        db.session.commit()

    sample_job = Job.query.filter_by(title="python developer").first()
    if not sample_job:
        sample_job = Job.query.first()

    parsed_res = sample_resume.get_parsed_data()
    job_data = {
        "title": sample_job.title,
        "company": sample_job.company,
        "location": sample_job.location,
        "required_skills": sample_job.get_required_skills(),
        "preferred_skills": sample_job.get_preferred_skills(),
        "experience": sample_job.experience_required,
        "education": sample_job.education_required,
        "description": sample_job.description
    }

    match_result = match_resume_to_job(
        parsed_res,
        job_data,
        raw_resume_text=sample_resume.extracted_text,
        raw_job_text=sample_job.description
    )

    demo_match = Match(
        user_id=user.id,
        resume_id=sample_resume.id,
        job_id=sample_job.id,
        job_title=sample_job.title,
        company_name=sample_job.company,
        overall_score=match_result["overall_score"],
        skill_score=match_result["breakdown"]["skill_score"],
        experience_score=match_result["breakdown"]["experience_score"],
        semantic_score=match_result["breakdown"]["semantic_score"],
        education_score=match_result["breakdown"]["education_score"],
        project_score=match_result["breakdown"]["project_score"]
    )
    demo_match.set_matched_skills(match_result["matched_skills"])
    demo_match.set_missing_skills(match_result["missing_skills"])
    demo_match.set_partial_skills(match_result["partial_skills"])
    demo_match.set_explanation(match_result["explanation"])
    demo_match.set_recommendations(match_result["recommendations"])

    db.session.add(demo_match)
    db.session.commit()

    return jsonify({
        "success": True,
        "match_id": demo_match.id,
        "redirect_url": url_for("matching.match_result_view", match_id=demo_match.id),
        "result": match_result
    })

@matching_bp.route("/api/matches", methods=["GET"])
@login_required
def api_get_matches():
    user_id = session.get("user_id")
    matches = Match.query.filter_by(user_id=user_id).order_by(Match.created_at.desc()).all()
    return jsonify({"success": True, "matches": [m.to_dict() for m in matches]})

@matching_bp.route("/api/matches/<int:match_id>", methods=["GET"])
@login_required
def api_get_match(match_id):
    user_id = session.get("user_id")
    match = Match.query.filter_by(id=match_id, user_id=user_id).first_or_404()
    return jsonify({"success": True, "match": match.to_dict()})

@matching_bp.route("/api/skills", methods=["GET"])
def api_get_skills():
    skills = Skill.query.all()
    return jsonify({"success": True, "skills": [s.to_dict() for s in skills]})
