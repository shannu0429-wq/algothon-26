from services.matching_engine import match_resume_to_job
from services.job_parser import parse_job_description

def rank_jobs_for_resume(parsed_resume, raw_resume_text, jobs_list):
    ranked = []
    for job in jobs_list:
        job_data = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "required_skills": job.get_required_skills(),
            "preferred_skills": job.get_preferred_skills(),
            "experience": job.experience_required,
            "education": job.education_required,
            "description": job.description,
            "job_type": job.job_type,
        }
        
        match_res = match_resume_to_job(
            parsed_resume,
            job_data,
            raw_resume_text=raw_resume_text,
            raw_job_text=job.description
        )

        job_dict = job.to_dict()
        job_dict["match_score"] = match_res["overall_score"]
        job_dict["match_category"] = match_res["category"]
        job_dict["matched_skills"] = match_res["matched_skills"]
        job_dict["missing_skills"] = match_res["missing_skills"]
        job_dict["partial_skills"] = match_res["partial_skills"]
        job_dict["breakdown"] = match_res["breakdown"]
        ranked.append(job_dict)

    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked
