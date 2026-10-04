import re
from services.skill_extractor import normalize_skill, extract_skills
from services.embedding_service import compute_semantic_similarity

DOMAIN_TAXONOMY = {
    "computer_science": [
        "python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang",
        "rust", "ruby", "php", "swift", "kotlin", "scala", "flask", "django", "fastapi",
        "react", "angular", "vue", "spring", "spring boot", "next.js", "sql", "mysql",
        "postgresql", "sqlite", "mongodb", "redis", "docker", "kubernetes", "aws", "azure",
        "gcp", "machine learning", "deep learning", "nlp", "ai", "artificial intelligence",
        "data science", "data analysis", "frontend", "backend", "full stack", "html", "css",
        "git", "rest api", "computer science", "software engineer", "developer", "web development",
        "algorithms", "data structures", "cloud", "devops", "ci/cd", "microservices", "software"
    ],
    "civil_engineering": [
        "civil", "civil engineering", "structural", "structural engineering", "autocad",
        "autocad civil 3d", "revit", "staad pro", "etabs", "bim", "surveying", "concrete",
        "concrete technology", "geotechnical", "site engineer", "construction", "construction management",
        "estimation", "quantity surveying", "primavera", "hydraulics", "foundation", "steel structures",
        "highway", "transportation engineering", "bridge", "rcc", "total station", "building planning",
        "structural analysis", "site engineering"
    ],
    "mechanical_engineering": [
        "mechanical", "mechanical engineering", "solidworks", "catia", "ansys", "autocad mechanical",
        "thermodynamics", "fluid mechanics", "heat transfer", "cnc machining", "gd&t",
        "finite element analysis", "fea", "cad/cam", "robotics", "mechatronics", "automotive",
        "manufacturing processes", "hvac", "piping"
    ],
    "electrical_engineering": [
        "electrical", "electrical engineering", "circuit design", "pcb design", "vlsi",
        "embedded systems", "microcontrollers", "verilog", "vhdl", "power systems",
        "plc", "scada", "fpga", "matlab", "simulink", "electronics", "telecommunication"
    ]
}

def detect_domain(skills, text=""):
    combined = " ".join([normalize_skill(s) for s in skills if s]) + " " + (text or "").lower()
    scores = {}
    for domain, kws in DOMAIN_TAXONOMY.items():
        score = 0
        for kw in kws:
            if kw in skills:
                score += 4
            pattern = r"\b" + re.escape(kw) + r"\b"
            matches = len(re.findall(pattern, combined))
            score += matches
        scores[domain] = score

    best_domain, max_pts = max(scores.items(), key=lambda x: x[1])
    if max_pts < 3:
        return "general", 0
    return best_domain, max_pts

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

def calculate_experience_score(resume_experience, job_experience_text, domain_aligned=True):
    if not domain_aligned:
        return 10.0

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
        return 25.0

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
        ratio = max(resume_years / max(req_years, 1.0), 0.3)

    score = ratio * 100.0
    return min(max(round(score, 1), 15.0), 100.0)

def calculate_education_score(resume_education, job_education_text, domain_aligned=True, job_domain="general", cand_domain="general"):
    if not resume_education:
        return 25.0

    if not domain_aligned:
        return 15.0

    job_edu = job_education_text.lower()
    highest_score = 50.0

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
            highest_score = max(highest_score, 60.0)

        field = edu.get("field", "").lower()
        if cand_domain == "computer_science" and any(f in field for f in ["computer", "data", "software", "information", "it"]):
            highest_score = min(highest_score + 5.0, 100.0)
        elif cand_domain == "civil_engineering" and any(f in field for f in ["civil", "structural", "construction"]):
            highest_score = min(highest_score + 5.0, 100.0)

    return min(max(round(highest_score, 1), 20.0), 100.0)

def calculate_project_score(resume_projects, job_text, domain_aligned=True):
    if not resume_projects:
        return 20.0

    if not domain_aligned:
        return 10.0

    proj_texts = []
    for p in resume_projects:
        name = p.get("name", "")
        desc = p.get("description", "")
        techs = " ".join(p.get("technologies", []))
        proj_texts.append(f"{name} {desc} {techs}".strip())

    combined_projects = " \n ".join(proj_texts)
    sim = compute_semantic_similarity(combined_projects, job_text)
    
    score = (sim * 80.0) + (min(len(resume_projects), 3) * 6.6)
    return min(max(round(score, 1), 15.0), 100.0)

def get_match_category(score, is_domain_mismatch=False):
    if is_domain_mismatch or score < 25.0:
        return "domain mismatch"
    elif score >= 90.0:
        return "excellent match"
    elif score >= 75.0:
        return "strong match"
    elif score >= 60.0:
        return "good match"
    elif score >= 40.0:
        return "moderate match"
    else:
        return "low match"

def generate_dynamic_explanation(matched_skills, missing_skills, partial_skills, score_breakdown, job_data, is_domain_mismatch=False, cand_domain="general", job_domain="general"):
    job_title = job_data.get("title", "role").lower()
    
    cand_label = cand_domain.replace("_", " ")
    job_label = job_domain.replace("_", " ")

    if is_domain_mismatch:
        alignment_text = f"domain mismatch detected: candidate background is specialized in {cand_label}, whereas this {job_title} role requires {job_label} expertise. zero core required technical skills were matched."
        project_text = f"existing project portfolio reflects {cand_label} implementations and does not demonstrate required practical workflows in {job_label}."
        experience_text = f"prior work history focuses on {cand_label} and does not satisfy the specialized operational criteria of this {job_label} position."
        gap_sample = ", ".join(missing_skills[:4]) if missing_skills else job_label
        gap_text = f"critical domain prerequisites ({gap_sample}) are completely absent from the candidate profile."
        return {
            "technical_alignment": alignment_text,
            "project_experience": project_text,
            "experience_fit": experience_text,
            "skill_gap": gap_text
        }

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

def generate_recommendations(missing_skills, partial_skills, score_breakdown, is_domain_mismatch=False, cand_domain="general", job_domain="general"):
    recommendations = []
    
    cand_label = cand_domain.replace("_", " ")
    job_label = job_domain.replace("_", " ")

    if is_domain_mismatch:
        recommendations.append(f"this position belongs to {job_label}. for your {cand_label} background, apply for software, backend, or data engineering roles for 85%+ compatibility.")
        recommendations.append(f"if transitioning to {job_label}, acquire formal certifications in core prerequisites such as {', '.join(missing_skills[:3])}.")
        recommendations.append("highlight cross-disciplinary computational skills such as technical simulations or numerical modeling.")
        return recommendations

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

    job_full_text = (raw_job_text or job_data.get("description", "") + " " + job_data.get("title", "")).lower()
    resume_full_text = (raw_resume_text or " ".join(resume_skills) + " " + parsed_resume.get("summary", "")).lower()

    cand_domain, cand_pts = detect_domain(resume_skills, resume_full_text)
    job_domain, job_pts = detect_domain(job_req_skills + job_pref_skills, job_full_text)

    is_domain_mismatch = (
        cand_domain != "general" and
        job_domain != "general" and
        cand_domain != job_domain and
        len(skills_res["matched"]) == 0
    )

    domain_aligned = not is_domain_mismatch

    exp_score = calculate_experience_score(parsed_resume.get("experience", []), job_data.get("experience", "1-3 years"), domain_aligned=domain_aligned)
    edu_score = calculate_education_score(parsed_resume.get("education", []), job_data.get("education", "bachelor's degree"), domain_aligned=domain_aligned, job_domain=job_domain, cand_domain=cand_domain)
    proj_score = calculate_project_score(parsed_resume.get("projects", []), job_full_text, domain_aligned=domain_aligned)

    sem_similarity = compute_semantic_similarity(resume_full_text, job_full_text)
    raw_sem_score = round(sem_similarity * 100.0, 1)

    if is_domain_mismatch:
        semantic_score = min(raw_sem_score * 0.25, 12.0)
        skill_score = 0.0
        exp_score = min(exp_score, 12.0)
        edu_score = min(edu_score, 15.0)
        proj_score = min(proj_score, 8.0)
    else:
        if len(skills_res["matched"]) == 0:
            semantic_score = min(raw_sem_score * 0.4, 25.0)
            exp_score = min(exp_score * 0.4, 30.0)
            edu_score = min(edu_score * 0.4, 30.0)
            proj_score = min(proj_score * 0.3, 20.0)
        else:
            semantic_score = min(max(raw_sem_score, 10.0), 100.0)

    overall = (
        (skill_score * 0.40) +
        (exp_score * 0.20) +
        (semantic_score * 0.20) +
        (edu_score * 0.10) +
        (proj_score * 0.10)
    )

    if is_domain_mismatch:
        overall_score = min(round(overall, 1), 9.5)
    elif len(skills_res["matched"]) == 0:
        overall_score = min(round(overall, 1), 18.0)
    else:
        overall_score = min(max(round(overall, 1), 5.0), 100.0)

    score_breakdown = {
        "overall_score": overall_score,
        "skill_score": round(skill_score, 1),
        "experience_score": round(exp_score, 1),
        "semantic_score": round(semantic_score, 1),
        "education_score": round(edu_score, 1),
        "project_score": round(proj_score, 1),
    }

    category = get_match_category(overall_score, is_domain_mismatch=is_domain_mismatch)
    explanation = generate_dynamic_explanation(
        skills_res["matched"],
        skills_res["missing"],
        skills_res["partial"],
        score_breakdown,
        job_data,
        is_domain_mismatch=is_domain_mismatch,
        cand_domain=cand_domain,
        job_domain=job_domain
    )
    recommendations = generate_recommendations(
        skills_res["missing"],
        skills_res["partial"],
        score_breakdown,
        is_domain_mismatch=is_domain_mismatch,
        cand_domain=cand_domain,
        job_domain=job_domain
    )

    return {
        "overall_score": overall_score,
        "category": category,
        "breakdown": score_breakdown,
        "matched_skills": skills_res["matched"],
        "missing_skills": skills_res["missing"],
        "partial_skills": skills_res["partial"],
        "explanation": explanation,
        "recommendations": recommendations,
        "is_domain_mismatch": is_domain_mismatch,
        "candidate_domain": cand_domain,
        "job_domain": job_domain
    }
