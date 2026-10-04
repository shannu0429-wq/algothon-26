import re

SKILL_TAXONOMY = {
    "programming languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang",
        "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "dart",
        "perl", "shell", "bash", "powershell", "lua", "julia"
    ],
    "frameworks": [
        "flask", "django", "fastapi", "express", "express.js", "react", "react.js",
        "angular", "vue", "vue.js", "spring", "spring boot", "asp.net", "asp.net core",
        "laravel", "ruby on rails", "rails", "next.js", "nestjs", "flutter",
        "react native", "svelte", "torch", "pytorch", "tensorflow", "keras"
    ],
    "databases": [
        "sql", "mysql", "postgresql", "postgres", "sqlite", "mongodb", "redis", "cassandra",
        "oracle", "sql server", "microsoft sql server", "elasticsearch", "dynamodb",
        "mariadb", "neo4j", "couchbase", "firestore", "supabase"
    ],
    "cloud": [
        "aws", "amazon web services", "azure", "microsoft azure", "google cloud",
        "google cloud platform", "gcp", "heroku", "digitalocean", "cloudflare",
        "openstack", "serverless", "aws lambda", "ec2", "s3", "cloud storage"
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "jenkins", "gitlab ci", "github actions",
        "terraform", "ansible", "helm", "prometheus", "grafana", "ci/cd",
        "continuous integration", "continuous deployment", "nginx", "apache",
        "linux", "unix", "bash scripting"
    ],
    "ai/ml": [
        "machine learning", "deep learning", "natural language processing", "nlp",
        "computer vision", "artificial intelligence", "ai", "neural networks",
        "pytorch", "tensorflow", "keras", "scikit-learn", "huggingface", "llm",
        "large language models", "langchain", "transformers", "opencv",
        "generative ai", "genai", "prompt engineering", "reinforcement learning"
    ],
    "data": [
        "data analysis", "data science", "data engineering", "etl", "spark",
        "apache spark", "hadoop", "airflow", "tableau", "power bi", "bigquery",
        "snowflake", "pandas", "numpy", "scipy", "data visualization",
        "data modeling", "data pipelines"
    ],
    "web": [
        "html", "html5", "css", "css3", "rest api", "restful api", "restful apis",
        "rest apis", "rest", "graphql", "websockets", "tailwind css", "tailwind",
        "bootstrap", "responsive design", "json", "xml", "ajax", "web development",
        "frontend development", "backend development", "full stack development"
    ],
    "mobile": [
        "android", "ios", "flutter", "react native", "swift", "kotlin",
        "mobile app development", "xcode", "android studio"
    ],
    "tools": [
        "git", "github", "gitlab", "jira", "confluence", "postman", "vs code",
        "visual studio code", "pycharm", "figma", "docker desktop", "npm", "pip",
        "vite", "webpack"
    ],
    "soft skills": [
        "communication", "leadership", "problem solving", "teamwork", "adaptability",
        "critical thinking", "collaboration", "agile", "scrum", "project management",
        "time management", "analytical skills", "creativity", "presentation skills",
        "cross-functional collaboration"
    ]
}

SYNONYM_MAP = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "react.js": "react",
    "reactjs": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "express.js": "express",
    "expressjs": "express",
    "nextjs": "next.js",
    "postgres": "postgresql",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "google cloud platform": "google cloud",
    "gcp": "google cloud",
    "microsoft azure": "azure",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "dl": "deep learning",
    "genai": "generative ai",
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    "continuous integration": "ci/cd",
    "continuous deployment": "ci/cd",
    "visual studio code": "vs code",
    "structured query language": "sql",
}

def normalize_skill(skill):
    if not skill:
        return ""
    clean = skill.strip().lower()
    clean = re.sub(r"\s+", " ", clean)
    return SYNONYM_MAP.get(clean, clean)

def get_skill_category(skill_name):
    norm = normalize_skill(skill_name)
    for cat, skills in SKILL_TAXONOMY.items():
        norm_skills = [normalize_skill(s) for s in skills]
        if norm in norm_skills:
            return cat
    return "tools"

def extract_skills(text):
    if not text:
        return {"skills_by_category": {}, "all_skills": []}

    cleaned_text = text.lower()
    cleaned_text = re.sub(r"[,\(\)\[\]\{\}\/\\;:]", " ", cleaned_text)
    words = set(re.findall(r"\b[a-z0-9#+.]+\b", cleaned_text))

    detected_skills = set()
    category_map = {cat: set() for cat in SKILL_TAXONOMY}

    for category, skill_list in SKILL_TAXONOMY.items():
        for skill in skill_list:
            norm_target = normalize_skill(skill)
            if " " in skill or "." in skill or "+" in skill or "#" in skill or "-" in skill:
                pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill) + r"(?![a-zA-Z0-9])"
                if re.search(pattern, cleaned_text):
                    detected_skills.add(norm_target)
                    category_map[category].add(norm_target)
            else:
                if skill in words:
                    detected_skills.add(norm_target)
                    category_map[category].add(norm_target)

    for abbrev, full in SYNONYM_MAP.items():
        if " " not in abbrev:
            if abbrev in words:
                detected_skills.add(full)
                cat = get_skill_category(full)
                category_map[cat].add(full)
        else:
            if re.search(r"\b" + re.escape(abbrev) + r"\b", cleaned_text):
                detected_skills.add(full)
                cat = get_skill_category(full)
                category_map[cat].add(full)

    formatted_categories = {}
    for cat, skills in category_map.items():
        if skills:
            formatted_categories[cat] = sorted(list(skills))

    return {
        "skills_by_category": formatted_categories,
        "all_skills": sorted(list(detected_skills))
    }
