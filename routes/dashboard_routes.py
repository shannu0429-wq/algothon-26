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

    return render_template("profile.html", user=user)

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

@dashboard_bp.route("/database")
@login_required
def database_details_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id)

    user_count = User.query.count()
    resume_count = Resume.query.count()
    job_count = Job.query.count()
    match_count = Match.query.count()
    skill_count = Skill.query.count()

    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_resumes = Resume.query.order_by(Resume.uploaded_at.desc()).limit(10).all()
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(10).all()
    recent_matches = Match.query.order_by(Match.created_at.desc()).limit(10).all()

    from collections import Counter
    all_skills = Skill.query.all()
    cat_counts = Counter([s.category for s in all_skills])

    from config import Config
    db_info = {
        "host": Config.MYSQL_HOST,
        "port": Config.MYSQL_PORT,
        "database": Config.MYSQL_DATABASE,
        "user": Config.MYSQL_USER,
        "driver": "mysql+pymysql"
    }

    return render_template(
        "database.html",
        user=user,
        db_info=db_info,
        user_count=user_count,
        resume_count=resume_count,
        job_count=job_count,
        match_count=match_count,
        skill_count=skill_count,
        recent_users=recent_users,
        recent_resumes=recent_resumes,
        recent_jobs=recent_jobs,
        recent_matches=recent_matches,
        cat_counts=cat_counts.most_common()
    )

@dashboard_bp.route("/how-it-works")
def how_it_works_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    return render_template("how_it_works.html", user=user)
