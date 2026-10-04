import re
from services.skill_extractor import extract_skills, normalize_skill, SKILL_TAXONOMY

def parse_job_description(text, default_title="", default_company="", default_location=""):
    if not text:
        return {
            "title": default_title.lower(),
            "company": default_company.lower(),
            "location": default_location.lower(),
            "required_skills": [],
            "preferred_skills": [],
            "experience": "1-3 years",
            "education": "bachelor's degree",
            "responsibilities": [],
            "technologies": [],
            "domain": "software engineering",
            "soft_skills": []
        }

    lower_text = text.lower()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    title = default_title.lower()
    if not title:
        title_patterns = [
            r"\b(?:job title|position|role)[:\t ]+([^\r\n,;]+)",
            r"\b((?:senior|junior|lead|principal|staff|associate)?\s*(?:software engineer|backend engineer|frontend engineer|full stack engineer|data scientist|data engineer|machine learning engineer|ai engineer|devops engineer|cloud architect|systems analyst|product manager))\b"
        ]
        for pat in title_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                title = m.group(1).strip().lower()
                break
        if not title and lines:
            if len(lines[0].split()) <= 6:
                title = lines[0].lower()
            else:
                title = "software engineer"

    company = default_company.lower()
    if not company:
        comp_match = re.search(r"\b(?:company|organization|employer|about)[:\t ]+([^\r\n,;]+)", text, re.IGNORECASE)
        if comp_match:
            company = comp_match.group(1).strip().lower()
        elif len(lines) > 1 and len(lines[1].split()) <= 4:
            company = lines[1].lower()
        else:
            company = "innovative tech solutions"

    location = default_location.lower()
    if not location:
        loc_match = re.search(r"\b(?:location|workplace|office)[:\s]+([a-zA-Z0-9\s,]{2,35})\b", text, re.IGNORECASE)
        if loc_match:
            location = loc_match.group(1).strip().lower()
        elif "remote" in lower_text:
            location = "remote"
        elif "hybrid" in lower_text:
            location = "hybrid"
        else:
            location = "san francisco, ca"

    exp_match = re.search(r"\b(\d{1,2}(?:\s*-\s*\d{1,2})?\+?\s*(?:years?|yrs?)(?:\s*of\s*experience)?)\b", lower_text)
    if exp_match:
        experience = exp_match.group(1).lower()
    elif "entry level" in lower_text or "junior" in lower_text:
        experience = "0-2 years"
    elif "senior" in lower_text or "lead" in lower_text:
        experience = "5+ years"
    else:
        experience = "2-4 years"

    edu_match = re.search(r"\b(bachelor'?s|master'?s|ph\.?d|b\.?tech|b\.?e|m\.?s|degree in [a-zA-Z\s]+)\b", lower_text)
    if edu_match:
        education = edu_match.group(0).lower()
    else:
        education = "bachelor's degree in computer science or related field"

    req_section = ""
    pref_section = ""
    resp_section = ""

    req_match = re.search(r"(?:requirements|qualifications|must have|what you bring)[:\n](.*?)(?=(?:preferred|nice to have|responsibilities|benefits|about us|\Z))", text, re.IGNORECASE | re.DOTALL)
    if req_match:
        req_section = req_match.group(1)

    pref_match = re.search(r"(?:preferred|nice to have|bonus points|good to have)[:\n](.*?)(?=(?:responsibilities|requirements|qualifications|benefits|about us|\Z))", text, re.IGNORECASE | re.DOTALL)
    if pref_match:
        pref_section = pref_match.group(1)

    resp_match = re.search(r"(?:responsibilities|duties|what you will do|role overview)[:\n](.*?)(?=(?:requirements|qualifications|preferred|benefits|\Z))", text, re.IGNORECASE | re.DOTALL)
    if resp_match:
        resp_section = resp_match.group(1)

    all_extracted = extract_skills(text)
    req_skills = extract_skills(req_section)["all_skills"] if req_section else []
    pref_skills = extract_skills(pref_section)["all_skills"] if pref_section else []

    if not req_skills:
        req_skills = all_extracted["all_skills"][:8]
    if not pref_skills:
        pref_candidates = [s for s in all_extracted["all_skills"] if s not in req_skills]
        pref_skills = pref_candidates[:4]

    responsibilities = []
    source_resp = resp_section if resp_section else text
    for line in source_resp.split("\n"):
        clean_l = line.strip().lower()
        if (clean_l.startswith("-") or clean_l.startswith("•") or clean_l.startswith("*")) and len(clean_l.split()) >= 4:
            responsibilities.append(re.sub(r"^[-*•\s]+", "", clean_l))
    if not responsibilities:
        responsibilities = [
            "collaborate with cross-functional teams to design, develop, and deploy software features.",
            "write clean, maintainable, and well-tested code following best practices.",
            "participate in code reviews, technical discussions, and architecture planning."
        ]

    soft_skills = [s for s in all_extracted["all_skills"] if s in [normalize_skill(x) for x in SKILL_TAXONOMY["soft skills"]]]

    domains = ["fintech", "healthcare", "e-commerce", "artificial intelligence", "cloud infrastructure", "cybersecurity", "saas", "edtech"]
    domain = "cloud software & ai"
    for d in domains:
        if d in lower_text:
            domain = d
            break

    return {
        "title": title,
        "company": company,
        "location": location,
        "required_skills": req_skills,
        "preferred_skills": pref_skills,
        "experience": experience,
        "education": education,
        "responsibilities": responsibilities[:6],
        "technologies": all_extracted["all_skills"],
        "domain": domain,
        "soft_skills": soft_skills
    }
