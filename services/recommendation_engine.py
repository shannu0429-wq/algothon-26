from collections import Counter
from services.skill_extractor import normalize_skill, get_skill_category

def get_recommended_skills_for_user(user_skills, target_jobs, top_n=8):
    norm_user_skills = {normalize_skill(s) for s in user_skills if s}
    missing_counter = Counter()

    for job in target_jobs:
        req_skills = job.get_required_skills() if hasattr(job, "get_required_skills") else job.get("required_skills", [])
        pref_skills = job.get_preferred_skills() if hasattr(job, "get_preferred_skills") else job.get("preferred_skills", [])
        
        for sk in req_skills + pref_skills:
            norm = normalize_skill(sk)
            if norm and norm not in norm_user_skills:
                missing_counter[norm] += 1

    recommended = []
    for skill_name, count in missing_counter.most_common(top_n):
        category = get_skill_category(skill_name)
        recommended.append({
            "name": skill_name.lower(),
            "category": category.lower(),
            "demand_frequency": count
        })

    return recommended
