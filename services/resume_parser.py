import re
from services.skill_extractor import extract_skills

SECTION_PATTERNS = {
    "education": [
        r"\b(?:education|academic background|qualifications|academic history|degrees|academic record)\b"
    ],
    "experience": [
        r"\b(?:work experience|professional experience|employment history|experience|work history|career history|internships|professional background)\b"
    ],
    "skills": [
        r"\b(?:technical skills|skills|core competencies|areas of expertise|technical stack|technologies|proficiencies|skills & tools)\b"
    ],
    "projects": [
        r"\b(?:projects|personal projects|technical projects|academic projects|key projects|featured projects)\b"
    ],
    "certifications": [
        r"\b(?:certifications|certificates|licenses|credentials|accreditations|professional certifications)\b"
    ]
}

DEGREE_PATTERNS = [
    r"\b(?:bachelor of technology|b\.tech|btech|bachelor of engineering|b\.e\.|bachelor of science|b\.s\.|bs|bachelor of arts|b\.a\.|ba|bachelor's|bachelors)\b",
    r"\b(?:master of technology|m\.tech|mtech|master of science|m\.s\.|ms|master of business administration|mba|master's|masters|m\.e\.)\b",
    r"\b(?:ph\.d\.|phd|doctor of philosophy|doctorate)\b",
    r"\b(?:associate degree|diploma|higher secondary|secondary school)\b"
]

def extract_contact_info(text):
    info = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
        "portfolio": ""
    }

    email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)
    if email_match:
        info["email"] = email_match.group(0).lower()

    phone_patterns = [
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        r"\+?\d{1,3}[-.\s]?\d{10}",
        r"\b\d{10}\b"
    ]
    for p in phone_patterns:
        phone_match = re.search(p, text)
        if phone_match:
            info["phone"] = phone_match.group(0).strip().lower()
            break

    linkedin_match = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
    if linkedin_match:
        info["linkedin"] = linkedin_match.group(0).lower()

    github_match = re.search(r"(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9_-]+", text, re.IGNORECASE)
    if github_match:
        info["github"] = github_match.group(0).lower()

    portfolio_match = re.search(r"(?:https?:\/\/)?(?:www\.)?[a-zA-Z0-9-]+\.(?:dev|me|io|app|site|net|org)(?:\/[^\s]*)?", text, re.IGNORECASE)
    if portfolio_match:
        found_url = portfolio_match.group(0).lower()
        if "linkedin.com" not in found_url and "github.com" not in found_url:
            info["portfolio"] = found_url

    location_patterns = [
        r"\b([a-zA-Z\s]{2,25},\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|USA|India|UK|Canada|Germany))\b",
        r"\b(?:location|address|city)[:\s]+([a-zA-Z\s,]+)\b"
    ]
    for loc_pat in location_patterns:
        loc_match = re.search(loc_pat, text, re.IGNORECASE)
        if loc_match:
            cand = loc_match.group(1).strip().lower()
            if len(cand) < 40 and not any(k in cand for k in ["university", "college", "school"]):
                info["location"] = cand
                break

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:5]:
        lower_line = line.lower()
        if (
            not info["email"] in lower_line
            and not (info["phone"] and info["phone"] in lower_line)
            and "linkedin" not in lower_line
            and "github" not in lower_line
            and "resume" not in lower_line
            and "curriculum" not in lower_line
            and len(line.split()) <= 4
            and re.match(r"^[a-zA-Z\s.'-]+$", line)
        ):
            info["name"] = re.sub(r"\s+", " ", line.strip().lower())
            break

    if not info["name"] and info["email"]:
        alias = info["email"].split("@")[0]
        cleaned_alias = re.sub(r"[\._0-9]", " ", alias).strip()
        if cleaned_alias:
            info["name"] = cleaned_alias.lower()

    return info

def split_into_sections(text):
    lines = text.split("\n")
    sections = {}
    current_section = "summary"
    sections[current_section] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        detected_sec = None
        clean_header = re.sub(r"^[\s=\-*_#~•|:>]+|[\s=\-*_#~•|:<]+$", "", stripped).strip()
        if len(clean_header) < 50:
            for sec_name, patterns in SECTION_PATTERNS.items():
                for pat in patterns:
                    if re.match(rf"^(?:[-*•#\d.]*\s*)?{pat}[:\s]*$", clean_header, re.IGNORECASE):
                        detected_sec = sec_name
                        break
                if detected_sec:
                    break

        if detected_sec:
            current_section = detected_sec
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(stripped)

    result = {}
    for k, v in sections.items():
        result[k] = "\n".join(v).strip()
    return result

def parse_education(edu_text):
    if not edu_text:
        return []

    entries = []
    lines = edu_text.split("\n")
    current_entry = {
        "degree": "bachelor's degree",
        "institution": "",
        "field": "",
        "graduation_year": "",
        "gpa": ""
    }
    
    found_any = False
    for line in lines:
        lower_line = line.lower()
        
        for deg_pat in DEGREE_PATTERNS:
            match = re.search(deg_pat, lower_line)
            if match:
                current_entry["degree"] = match.group(0).lower()
                found_any = True
                break

        inst_patterns = [
            r"\b([a-zA-Z\s]*(?:university|college|institute|academy|school)[a-zA-Z\s]*)\b"
        ]
        for inst_pat in inst_patterns:
            inst_match = re.search(inst_pat, lower_line)
            if inst_match:
                inst_cand = inst_match.group(0).strip()
                if len(inst_cand) < 60:
                    current_entry["institution"] = inst_cand.lower()
                    found_any = True
                    break

        year_match = re.search(r"\b(19\d{2}|20\d{2})(?:\s*[-–]\s*(19\d{2}|20\d{2}|present|current))?\b", lower_line)
        if year_match:
            current_entry["graduation_year"] = year_match.group(0).lower()
            found_any = True

        gpa_match = re.search(r"\b(?:gpa|cgpa)[:\s]*([0-9]\.[0-9]{1,2}(?:\s*\/\s*[0-9](?:\.[0-9])?)?)\b", lower_line)
        if not gpa_match:
            gpa_match = re.search(r"\b([0-9]{2}(?:\.[0-9]+)?%)\b", lower_line)
        if gpa_match:
            current_entry["gpa"] = gpa_match.group(1).lower()
            found_any = True

        field_match = re.search(r"\b(?:in|of)\s+([a-zA-Z\s]{3,30}(?:computer science|engineering|information technology|data science|business|mathematics|physics|artificial intelligence))\b", lower_line)
        if field_match:
            current_entry["field"] = field_match.group(1).strip().lower()
            found_any = True

    if found_any or edu_text.strip():
        if not current_entry["institution"]:
            for line in lines:
                if len(line.split()) <= 6 and not re.search(r"\d", line):
                    current_entry["institution"] = line.strip().lower()
                    break
        entries.append(current_entry)
    return entries

def parse_experience(exp_text):
    if not exp_text:
        return []

    entries = []
    lines = exp_text.split("\n")
    chunks = []
    current_chunk = []

    for line in lines:
        is_date_line = bool(re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december|\d{4})\b.*?(?:present|current|\d{4})", line, re.IGNORECASE))
        if is_date_line and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
        else:
            current_chunk.append(line)
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    for chunk in chunks:
        ch_lines = [l.strip() for l in chunk.split("\n") if l.strip()]
        if not ch_lines:
            continue
        
        job_title = ""
        company = ""
        duration = ""
        responsibilities = []

        date_match = re.search(r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|[0-9]{1,2}\/)?\s*(?:19\d{2}|20\d{2})\s*[-–to\s]+\s*(?:present|current|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|[0-9]{1,2}\/)?\s*(?:19\d{2}|20\d{2})))", chunk, re.IGNORECASE)
        if date_match:
            duration = date_match.group(0).strip().lower()

        title_patterns = [
            r"\b((?:senior|junior|lead|principal|associate|staff)?\s*(?:software engineer|software developer|backend developer|frontend developer|full stack developer|web developer|data scientist|data analyst|machine learning engineer|ai engineer|devops engineer|cloud architect|qa engineer|product manager|intern))\b"
        ]
        for t_pat in title_patterns:
            t_match = re.search(t_pat, chunk, re.IGNORECASE)
            if t_match:
                job_title = t_match.group(1).strip().lower()
                break

        if not job_title and ch_lines:
            first_line = ch_lines[0]
            if len(first_line.split()) <= 6:
                job_title = first_line.lower()

        for l in ch_lines[:3]:
            lower_l = l.lower()
            if job_title and job_title in lower_l:
                parts = re.split(r"[-–|,@]", lower_l)
                if len(parts) > 1:
                    company = parts[1].strip()
            elif " at " in lower_l:
                parts = lower_l.split(" at ")
                if len(parts) > 1:
                    company = parts[1].strip()

        for l in ch_lines:
            lower_l = l.lower()
            if l.startswith("-") or l.startswith("•") or l.startswith("*") or len(l.split()) > 7:
                clean_bullet = re.sub(r"^[-*•\s]+", "", lower_l).strip()
                if clean_bullet and clean_bullet != job_title and clean_bullet != company:
                    responsibilities.append(clean_bullet)

        extracted_tech = extract_skills(chunk)["all_skills"]

        entries.append({
            "title": job_title if job_title else "software engineer",
            "company": company if company else "technology company",
            "duration": duration if duration else "experience recorded",
            "responsibilities": responsibilities[:5],
            "technologies": extracted_tech[:8]
        })

    return entries

def parse_projects(proj_text):
    if not proj_text:
        return []

    entries = []
    lines = [l.strip() for l in proj_text.split("\n") if l.strip()]
    current_proj = None

    for line in lines:
        lower_line = line.lower()
        if (
            len(line.split()) <= 6
            and not line.startswith("-")
            and not line.startswith("•")
            and not line.startswith("*")
            and not any(k in lower_line for k in ["github.com", "http", "www"])
        ):
            if current_proj:
                entries.append(current_proj)
            current_proj = {
                "name": line.lower(),
                "description": "",
                "technologies": []
            }
        else:
            if current_proj:
                if not current_proj["description"]:
                    current_proj["description"] = line.lower()
                else:
                    current_proj["description"] += " " + line.lower()

    if current_proj:
        entries.append(current_proj)

    for item in entries:
        item["technologies"] = extract_skills(item["name"] + " " + item["description"])["all_skills"][:6]

    return entries[:5]

def parse_certifications(cert_text):
    if not cert_text:
        return []

    certs = []
    lines = [l.strip() for l in cert_text.split("\n") if l.strip()]
    for line in lines:
        clean = re.sub(r"^[-*•\s]+", "", line).strip().lower()
        if len(clean) >= 4 and len(clean) <= 90:
            certs.append(clean)
    return certs[:8]

def parse_resume_content(raw_text):
    contact = extract_contact_info(raw_text)
    sections = split_into_sections(raw_text)
    skills_data = extract_skills(raw_text)
    education = parse_education(sections.get("education", ""))
    if not education:
        education = parse_education(raw_text)
    experience = parse_experience(sections.get("experience", ""))
    if not experience:
        experience = parse_experience(raw_text)
    projects = parse_projects(sections.get("projects", ""))
    if not projects:
        projects = parse_projects(raw_text)
    certifications = parse_certifications(sections.get("certifications", ""))
    if not certifications:
        certifications = parse_certifications(raw_text)

    summary_text = sections.get("summary", "")
    if len(summary_text.split()) > 100:
        summary_text = " ".join(summary_text.split()[:100])

    return {
        "personal_info": contact,
        "summary": summary_text.lower(),
        "education": education,
        "experience": experience,
        "skills": skills_data["all_skills"],
        "skills_by_category": skills_data["skills_by_category"],
        "projects": projects,
        "certifications": certifications
    }
