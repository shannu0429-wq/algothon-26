from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models import db, User, Resume, Job, Match, Skill
from routes.auth_routes import login_required
from services.ranking_engine import rank_jobs_for_resume
from services.recommendation_engine import get_recommended_skills_for_user

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return redirect(url_for("auth.login"))

    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    matches = Match.query.filter_by(user_id=user_id).order_by(Match.created_at.desc()).all()
    all_jobs = Job.query.order_by(Job.created_at.desc()).all()

    resume_analyzed = latest_resume is not None
    jobs_matched_count = len(matches)
    best_match_score = max([m.overall_score for m in matches], default=0.0)

    parsed_data = latest_resume.get_parsed_data() if latest_resume else {}
    detected_skills = parsed_data.get("skills", [])
    skills_detected_count = len(detected_skills)

    top_jobs = []
    if latest_resume and all_jobs:
        top_jobs = rank_jobs_for_resume(parsed_data, latest_resume.extracted_text, all_jobs)[:5]

    latest_match = matches[0] if matches else None

    missing_skills_sample = []
    if latest_match:
        missing_skills_sample = latest_match.get_missing_skills()[:6]

    recommendations_sample = []
    if latest_match:
        recommendations_sample = latest_match.get_recommendations()[:4]

    return render_template(
        "dashboard.html",
        user=user,
        resume_analyzed=resume_analyzed,
        latest_resume=latest_resume,
        jobs_matched_count=jobs_matched_count,
        best_match_score=round(best_match_score, 1),
        skills_detected_count=skills_detected_count,
        detected_skills=detected_skills[:12],
        top_jobs=top_jobs,
        latest_match=latest_match,
        missing_skills=missing_skills_sample,
        recommendations=recommendations_sample,
        recent_matches=matches[:5]
    )

@dashboard_bp.route("/skills")
@login_required
def skills_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    
    parsed = latest_resume.get_parsed_data() if latest_resume else {}
    user_skills = parsed.get("skills", [])
    categorized_skills = parsed.get("skills_by_category", {})

    all_jobs = Job.query.all()
    recommended_skills = get_recommended_skills_for_user(user_skills, all_jobs, top_n=10)

    return render_template(
        "skills.html",
        user=user,
        user_skills=user_skills,
        categorized_skills=categorized_skills,
        recommended_skills=recommended_skills,
        has_resume=latest_resume is not None
    )

@dashboard_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip().lower()
        location = request.form.get("location", "").strip().lower()
        linkedin = request.form.get("linkedin", "").strip().lower()
        github = request.form.get("github", "").strip().lower()
        portfolio = request.form.get("portfolio", "").strip().lower()
        career_interests = request.form.get("career_interests", "").strip().lower()

        if name:
            user.name = name
            session["user_name"] = name
        user.location = location
        user.linkedin = linkedin
        user.github = github
        user.portfolio = portfolio
        user.career_interests = career_interests

        db.session.commit()
        flash("profile updated successfully.", "success")
        return redirect(url_for("dashboard.profile_view"))

    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    matches = Match.query.filter_by(user_id=user_id).order_by(Match.created_at.desc()).all()
    parsed_data = latest_resume.get_parsed_data() if latest_resume else {}
    detected_skills = parsed_data.get("skills", [])
    candidate_education = parsed_data.get("education", [])
    candidate_experience = parsed_data.get("experience", [])
    best_match_score = max([m.overall_score for m in matches], default=0.0)

    from services.matching_engine import detect_domain
    cand_domain, _ = detect_domain(detected_skills, latest_resume.extracted_text if latest_resume else "")

    return render_template(
        "profile.html",
        user=user,
        latest_resume=latest_resume,
        parsed_data=parsed_data,
        detected_skills=detected_skills,
        candidate_education=candidate_education,
        candidate_experience=candidate_experience,
        matches_count=len(matches),
        best_match_score=round(best_match_score, 1),
        candidate_domain=cand_domain
    )

@dashboard_bp.route("/api/profile/skills/add", methods=["POST"])
@login_required
def api_add_profile_skill():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"success": False, "error": "user not authenticated."}), 401

    data = request.get_json() or request.form.to_dict() or {}
    raw_skill = data.get("skill", "").strip().lower()

    if not raw_skill:
        return jsonify({"success": False, "error": "please specify a skill name."}), 400

    from services.skill_extractor import normalize_skill, extract_skills
    norm_sk = normalize_skill(raw_skill)

    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    if not latest_resume:
        initial_text = f"candidate profile for {user.name}.\ntechnical skills: {norm_sk}"
        parsed = {
            "personal_info": {"name": user.name, "email": user.email, "location": user.location},
            "summary": f"candidate profile specialized in {user.career_interests or norm_sk}.",
            "skills": [norm_sk],
            "skills_by_category": {"programming_languages": [norm_sk]},
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": []
        }
        latest_resume = Resume(
            user_id=user_id,
            filename="profile_skills_resume.txt",
            extracted_text=initial_text
        )
        latest_resume.set_parsed_data(parsed)
        db.session.add(latest_resume)
    else:
        parsed = latest_resume.get_parsed_data()
        current_skills = parsed.get("skills", [])
        if norm_sk not in current_skills:
            current_skills.append(norm_sk)
            parsed["skills"] = current_skills
            re_extracted = extract_skills(" ".join(current_skills))
            parsed["skills_by_category"] = re_extracted["skills_by_category"]
            latest_resume.set_parsed_data(parsed)
            latest_resume.extracted_text += f"\n{norm_sk}"

    existing_skill_record = Skill.query.filter_by(name=norm_sk).first()
    if not existing_skill_record:
        cat = "technical skills"
        for c, sk_list in parsed.get("skills_by_category", {}).items():
            if norm_sk in sk_list:
                cat = c.replace("_", " ")
                break
        new_sk = Skill(name=norm_sk, category=cat)
        db.session.add(new_sk)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"skill '{norm_sk}' added successfully.",
        "skills": parsed.get("skills", []),
        "skill": norm_sk
    })

@dashboard_bp.route("/api/profile/skills/remove", methods=["POST"])
@login_required
def api_remove_profile_skill():
    user_id = session.get("user_id")
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    if not latest_resume:
        return jsonify({"success": False, "error": "no active resume or profile found."}), 404

    data = request.get_json() or request.form.to_dict() or {}
    target_skill = data.get("skill", "").strip().lower()

    from services.skill_extractor import normalize_skill, extract_skills
    norm_sk = normalize_skill(target_skill)

    parsed = latest_resume.get_parsed_data()
    current_skills = parsed.get("skills", [])
    if norm_sk in current_skills:
        current_skills = [s for s in current_skills if s != norm_sk]
        parsed["skills"] = current_skills
        re_extracted = extract_skills(" ".join(current_skills))
        parsed["skills_by_category"] = re_extracted["skills_by_category"]
        latest_resume.set_parsed_data(parsed)
        db.session.commit()

    return jsonify({
        "success": True,
        "message": f"skill '{norm_sk}' removed successfully.",
        "skills": current_skills
    })

@dashboard_bp.route("/api/profile/skills/sync", methods=["POST"])
@login_required
def api_sync_profile_skills():
    user_id = session.get("user_id")
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first()
    if not latest_resume:
        return jsonify({"success": False, "error": "no active resume to sync."}), 404

    from services.skill_extractor import extract_skills
    extracted = extract_skills(latest_resume.extracted_text)
    parsed = latest_resume.get_parsed_data()
    merged_skills = sorted(list(set(parsed.get("skills", []) + extracted["all_skills"])))
    parsed["skills"] = merged_skills
    re_extracted = extract_skills(" ".join(merged_skills))
    parsed["skills_by_category"] = re_extracted["skills_by_category"]
    latest_resume.set_parsed_data(parsed)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"{len(merged_skills)} skills synchronized from resume.",
        "skills": merged_skills
    })

@dashboard_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not user.check_password(current_password):
            flash("incorrect current password.", "error")
            return render_template("settings.html", user=user)

        if len(new_password) < 6:
            flash("new password must be at least 6 characters.", "error")
            return render_template("settings.html", user=user)

        if new_password != confirm_password:
            flash("passwords do not match.", "error")
            return render_template("settings.html", user=user)

        user.set_password(new_password)
        db.session.commit()
        flash("password changed successfully.", "success")
        return redirect(url_for("dashboard.settings_view"))

    return render_template("settings.html", user=user)

@dashboard_bp.route("/api/account/delete", methods=["POST"])
@login_required
def api_delete_account():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return jsonify({"success": False, "error": "user not found."}), 404

    data = request.get_json() or request.form.to_dict() or {}
    password = data.get("password", "").strip()
    confirmation = data.get("confirmation", "").strip().lower()

    if confirmation != "delete" and password and not user.check_password(password):
        return jsonify({"success": False, "error": "incorrect verification. account deletion aborted."}), 400

    db.session.delete(user)
    db.session.commit()
    session.clear()

    return jsonify({
        "success": True,
        "message": "your account and all associated data have been permanently deleted.",
        "redirect_url": url_for("index")
    })

@dashboard_bp.route("/settings/delete-account", methods=["POST"])
@login_required
def delete_account_form():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return redirect(url_for("index"))

    password = request.form.get("password", "").strip()
    confirmation = request.form.get("confirmation", "").strip().lower()

    if confirmation != "delete" and not user.check_password(password):
        flash("please enter your password or type 'delete' to confirm account deletion.", "error")
        return redirect(url_for("dashboard.settings_view"))

    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash("your account and all associated data have been permanently deleted.", "info")
    return redirect(url_for("index"))

@dashboard_bp.route("/database")
def database_details_view():
    return redirect(url_for("dashboard.dashboard_view"))

@dashboard_bp.route("/how-it-works")
def how_it_works_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    return render_template("how_it_works.html", user=user)
