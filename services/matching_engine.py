import re
from services.skill_extractor import normalize_skill, extract_skills
from services.embedding_service import compute_semantic_similarity

def calculate_skills_score(resume_skills, job_req_skills, job_pref_skills):
    norm_resume = {normalize_skill(s) for s in resume_skills if s}
    norm_req = [normalize_skill(s) for s in job_req_skills if s]
    norm_pref = [normalize_skill(s) for s in job_pref_skills if s]

    matched = []
    missing = []
    partial = []

    for req in norm_req:
        if req in norm_resume:
            matched.append(req)
        else:
            found_partial = False
            for res_sk in norm_resume:
                if (res_sk in req or req in res_sk) and len(res_sk) > 2 and len(req) > 2:
                    partial.append({
                        "job_skill": req,
                        "resume_skill": res_sk,
                        "explanation": f"partial match — {res_sk} experience was detected, but {req} was not explicitly identified."
                    })
                    found_partial = True
                    break
            if not found_partial:
                missing.append(req)

    for pref in norm_pref:
        if pref in norm_resume:
            if pref not in matched:
                matched.append(pref)
        else:
            if pref not in missing and not any(p["job_skill"] == pref for p in partial):
                found_partial = False
                for res_sk in norm_resume:
                    if (res_sk in pref or pref in res_sk) and len(res_sk) > 2 and len(pref) > 2:
                        partial.append({
                            "job_skill": pref,
                            "resume_skill": res_sk,
                            "explanation": f"partial match — {res_sk} experience was detected, but {pref} was not explicitly identified."
                        })
                        found_partial = True
                        break
                if not found_partial:
                    missing.append(pref)

    total_req_count = max(len(norm_req), 1)
    req_match_ratio = len([m for m in matched if m in norm_req]) / total_req_count
    partial_ratio = len(partial) / total_req_count
    pref_match_ratio = (len([m for m in matched if m in norm_pref]) / max(len(norm_pref), 1)) if norm_pref else 1.0

    skill_score = (req_match_ratio * 75.0) + (partial_ratio * 15.0) + (pref_match_ratio * 10.0)
    skill_score = min(max(skill_score, 0.0), 100.0)

    return {
        "score": round(skill_score, 1),
        "matched": sorted(list(set(matched))),
        "missing": sorted(list(set(missing))),
        "partial": partial
    }

def calculate_experience_score(resume_experience, job_experience_text):
    exp_text = job_experience_text.lower()
    req_years = 1.0
    year_match = re.search(r"(\d+)(?:\s*-\s*(\d+))?", exp_text)
    if year_match:
        if year_match.group(2):
            req_years = float(year_match.group(2))
        else:
            req_years = float(year_match.group(1))

    total_resume_items = len(resume_experience)
    if total_resume_items == 0:
        return 35.0

    resume_years = 0.0
    for exp in resume_experience:
        dur = exp.get("duration", "").lower()
        years_found = re.findall(r"\b(19\d{2}|20\d{2})\b", dur)
        if len(years_found) >= 2:
            try:
                y1 = int(years_found[0])
                y2 = int(years_found[1])
                diff = abs(y2 - y1)
                resume_years += max(diff, 1)
            except Exception:
                resume_years += 1.5
        elif "present" in dur or "current" in dur:
            resume_years += 2.0
        else:
            resume_years += 1.2

    if resume_years >= req_years:
        ratio = 1.0
    else:
        ratio = max(resume_years / max(req_years, 1.0), 0.4)

    score = ratio * 100.0
    return min(max(round(score, 1), 20.0), 100.0)

def calculate_education_score(resume_education, job_education_text):
    if not resume_education:
        return 50.0

    job_edu = job_education_text.lower()
    highest_score = 60.0

    for edu in resume_education:
        deg = edu.get("degree", "").lower()
        if "phd" in deg or "doctorate" in deg:
            highest_score = max(highest_score, 100.0)
        elif "master" in deg or "m.tech" in deg or "m.s." in deg or "mba" in deg:
            if "master" in job_edu or "phd" in job_edu:
                highest_score = max(highest_score, 95.0)
            else:
                highest_score = max(highest_score, 100.0)
        elif "bachelor" in deg or "b.tech" in deg or "b.e." in deg or "b.s." in deg:
            if "master" in job_edu or "phd" in job_edu:
                highest_score = max(highest_score, 75.0)
            else:
                highest_score = max(highest_score, 95.0)
        elif "associate" in deg or "diploma" in deg:
            highest_score = max(highest_score, 65.0)

        field = edu.get("field", "").lower()
        if any(f in field for f in ["computer", "data", "engineering", "technology", "information"]):
            highest_score = min(highest_score + 5.0, 100.0)

    return min(max(round(highest_score, 1), 30.0), 100.0)

def calculate_project_score(resume_projects, job_text):
    if not resume_projects:
        return 40.0

    proj_texts = []
    for p in resume_projects:
        name = p.get("name", "")
        desc = p.get("description", "")
        techs = " ".join(p.get("technologies", []))
        proj_texts.append(f"{name} {desc} {techs}".strip())

    combined_projects = " \n ".join(proj_texts)
    sim = compute_semantic_similarity(combined_projects, job_text)
    
    score = (sim * 80.0) + (min(len(resume_projects), 3) * 6.6)
    return min(max(round(score, 1), 35.0), 100.0)

def get_match_category(score):
    if score >= 90.0:
        return "excellent match"
    elif score >= 75.0:
        return "strong match"
    elif score >= 60.0:
        return "good match"
    elif score >= 40.0:
        return "moderate match"
    else:
        return "low match"

def generate_dynamic_explanation(matched_skills, missing_skills, partial_skills, score_breakdown, job_data):
    job_title = job_data.get("title", "role").lower()
    
    alignment_text = ""
    if matched_skills:
        top_matched = ", ".join(matched_skills[:5])
        alignment_text = f"{top_matched} experience detected in the resume strongly aligns with the technical requirements of this {job_title} role."
    else:
        alignment_text = f"foundational background was detected, but key core technologies for this {job_title} role require stronger alignment."

    project_text = ""
    if score_breakdown.get("project_score", 0) >= 70:
        project_text = "projects containing relevant software implementation and technical problem solving contribute positively to the match."
    else:
        project_text = "practical project exposure in the target domain could be further highlighted to enhance role readiness."

    experience_text = ""
    if score_breakdown.get("experience_score", 0) >= 75:
        experience_text = "demonstrated tenure and professional responsibilities correspond well with the requested seniority."
    else:
        experience_text = "the role seeks additional depth or verifiable years in specialized production environments."

    gap_text = ""
    if missing_skills:
        gap_sample = ", ".join(missing_skills[:3])
        gap_text = f"{gap_sample} was requested in the job description but was not detected in the resume."
    elif partial_skills:
        gap_text = "primary concepts are represented, though specific vendor implementations or specialized libraries were not explicitly identified."
    else:
        gap_text = "no critical technical skill gaps were detected for this profile."

    return {
        "technical_alignment": alignment_text,
        "project_experience": project_text,
        "experience_fit": experience_text,
        "skill_gap": gap_text
    }

def generate_recommendations(missing_skills, partial_skills, score_breakdown):
    recommendations = []
    
    if missing_skills:
        for sk in missing_skills[:4]:
            recommendations.append(f"add {sk} experience if applicable to demonstrate full tech stack coverage.")
    
    if partial_skills:
        for p in partial_skills[:2]:
            req = p.get("job_skill", "")
            recommendations.append(f"clarify explicit hands-on proficiency with {req} alongside your existing practical experience.")

    if score_breakdown.get("project_score", 0) < 75:
        recommendations.append("highlight relevant projects with measurable outcomes and specific architectural responsibilities.")

    if score_breakdown.get("experience_score", 0) < 70:
        recommendations.append("detail quantifiable impact, metrics, and team leadership in your recent role descriptions.")

    if not recommendations:
        recommendations.append("maintain current comprehensive project details and emphasize production achievements.")

    return recommendations[:5]

def match_resume_to_job(parsed_resume, job_data, raw_resume_text="", raw_job_text=""):
    resume_skills = parsed_resume.get("skills", [])
    job_req_skills = job_data.get("required_skills", [])
    job_pref_skills = job_data.get("preferred_skills", [])

    skills_res = calculate_skills_score(resume_skills, job_req_skills, job_pref_skills)
    skill_score = skills_res["score"]

    exp_score = calculate_experience_score(parsed_resume.get("experience", []), job_data.get("experience", "1-3 years"))
    edu_score = calculate_education_score(parsed_resume.get("education", []), job_data.get("education", "bachelor's degree"))
    proj_score = calculate_project_score(parsed_resume.get("projects", []), raw_job_text if raw_job_text else job_data.get("description", ""))

    resume_semantic_source = raw_resume_text if raw_resume_text else " ".join(resume_skills) + " " + parsed_resume.get("summary", "")
    job_semantic_source = raw_job_text if raw_job_text else job_data.get("description", "")
    sem_similarity = compute_semantic_similarity(resume_semantic_source, job_semantic_source)
    semantic_score = min(max(round(sem_similarity * 100.0, 1), 25.0), 100.0)

    overall = (
        (skill_score * 0.40) +
        (exp_score * 0.20) +
        (semantic_score * 0.20) +
        (edu_score * 0.10) +
        (proj_score * 0.10)
    )
    overall_score = min(max(round(overall, 1), 0.0), 100.0)

    score_breakdown = {
        "overall_score": overall_score,
        "skill_score": skill_score,
        "experience_score": exp_score,
        "semantic_score": semantic_score,
        "education_score": edu_score,
        "project_score": proj_score,
    }

    category = get_match_category(overall_score)
    explanation = generate_dynamic_explanation(
        skills_res["matched"],
        skills_res["missing"],
        skills_res["partial"],
        score_breakdown,
        job_data
    )
    recommendations = generate_recommendations(
        skills_res["missing"],
        skills_res["partial"],
        score_breakdown
    )

    return {
        "overall_score": overall_score,
        "category": category,
        "breakdown": score_breakdown,
        "matched_skills": skills_res["matched"],
        "missing_skills": skills_res["missing"],
        "partial_skills": skills_res["partial"],
        "explanation": explanation,
        "recommendations": recommendations
    }
