from flask import Blueprint, render_template, request, jsonify, session
from models import db, Job, Resume, User
from routes.auth_routes import login_required
from services.ranking_engine import rank_jobs_for_resume

job_bp = Blueprint("job", __name__)

@job_bp.route("/jobs")
def jobs_view():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first() if user_id else None

    query = Job.query
    keyword = request.args.get("q", "").strip().lower()
    location = request.args.get("location", "").strip().lower()
    job_type = request.args.get("type", "").strip().lower()
    experience = request.args.get("experience", "").strip().lower()
    sort_by = request.args.get("sort", "best_match").lower()
    min_score = float(request.args.get("min_score", 0))

    if keyword:
        query = query.filter(
            (Job.title.ilike(f"%{keyword}%")) |
            (Job.company.ilike(f"%{keyword}%")) |
            (Job.description.ilike(f"%{keyword}%")) |
            (Job.required_skills.ilike(f"%{keyword}%"))
        )

    if location and location != "all":
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if job_type and job_type != "all":
        query = query.filter(Job.job_type.ilike(f"%{job_type}%"))

    if experience and experience != "all":
        query = query.filter(Job.experience_required.ilike(f"%{experience}%"))

    all_matching_jobs = query.all()

    avg_score = 0
    candidate_skills = []
    if latest_resume:
        parsed_resume = latest_resume.get_parsed_data()
        candidate_skills = parsed_resume.get("skills", [])
        ranked = rank_jobs_for_resume(parsed_resume, latest_resume.extracted_text, all_matching_jobs)
        if min_score > 0:
            ranked = [j for j in ranked if j.get("match_score", 0) >= min_score]
        
        if sort_by == "highest_score" or sort_by == "best_match":
            ranked.sort(key=lambda x: x["match_score"], reverse=True)
        elif sort_by == "recently_added":
            ranked.sort(key=lambda x: x["created_at"] or "", reverse=True)
        displayed_jobs = ranked
        if displayed_jobs:
            avg_score = round(sum(j.get("match_score", 0) for j in displayed_jobs) / len(displayed_jobs), 1)
    else:
        displayed_jobs = [j.to_dict() for j in all_matching_jobs]
        if sort_by == "recently_added":
            displayed_jobs.sort(key=lambda x: x["created_at"] or "", reverse=True)

    unique_locations = sorted(list({j.location.lower() for j in Job.query.all() if j.location}))
    unique_types = sorted(list({j.job_type.lower() for j in Job.query.all() if j.job_type}))
    top_filter_skills = ["python", "react", "sql", "docker", "machine learning", "aws", "flask", "kubernetes"]

    return render_template(
        "jobs.html",
        user=user,
        jobs=displayed_jobs,
        has_resume=latest_resume is not None,
        resume=latest_resume,
        candidate_skills=candidate_skills[:8],
        avg_score=avg_score,
        locations=unique_locations,
        job_types=unique_types,
        top_filter_skills=top_filter_skills,
        selected_q=keyword,
        selected_location=location,
        selected_type=job_type,
        selected_sort=sort_by,
        selected_min_score=int(min_score),
        total_jobs_found=len(displayed_jobs)
    )

@job_bp.route("/jobs/<int:job_id>")
def job_details_view(job_id):
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    job = db.session.get(Job, job_id)
    if not job:
        from flask import abort
        abort(404)
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first() if user_id else None

    match_info = None
    if latest_resume:
        from services.matching_engine import match_resume_to_job
        parsed = latest_resume.get_parsed_data()
        match_info = match_resume_to_job(
            parsed,
            {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "required_skills": job.get_required_skills(),
                "preferred_skills": job.get_preferred_skills(),
                "experience": job.experience_required,
                "education": job.education_required,
                "description": job.description
            },
            raw_resume_text=latest_resume.extracted_text,
            raw_job_text=job.description
        )

    return render_template("job_details.html", user=user, job=job, match_info=match_info, has_resume=latest_resume is not None)

@job_bp.route("/api/jobs", methods=["GET"])
def api_get_jobs():
    user_id = session.get("user_id")
    latest_resume = Resume.query.filter_by(user_id=user_id).order_by(Resume.uploaded_at.desc()).first() if user_id else None

    jobs = Job.query.order_by(Job.created_at.desc()).all()
    if latest_resume:
        ranked = rank_jobs_for_resume(latest_resume.get_parsed_data(), latest_resume.extracted_text, jobs)
        return jsonify({"success": True, "jobs": ranked})
    
    return jsonify({"success": True, "jobs": [j.to_dict() for j in jobs]})

@job_bp.route("/api/jobs/<int:job_id>", methods=["GET"])
def api_get_job(job_id):
    job = Job.query.get_or_404(job_id)
    return jsonify({"success": True, "job": job.to_dict()})
