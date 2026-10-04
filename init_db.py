import os
import json
from flask import Flask
from config import Config
from models import db, User, Resume, Job, Match, Skill
from services.skill_extractor import SKILL_TAXONOMY, normalize_skill

SAMPLE_JOBS = [
    {
        "title": "python developer",
        "company": "apex analytics",
        "location": "remote",
        "description": "we are seeking a skilled python developer to build robust backend apis, data processing pipelines, and scalable microservices. the ideal candidate has deep expertise in python, flask, fastapi, and relational database systems.",
        "required_skills": ["python", "flask", "fastapi", "mysql", "rest api", "git"],
        "preferred_skills": ["docker", "redis", "celery", "aws"],
        "experience_required": "2-4 years",
        "education_required": "bachelor's degree in computer science or related field",
        "job_type": "full-time"
    },
    {
        "title": "backend developer",
        "company": "cloudscale systems",
        "location": "austin, tx",
        "description": "join our core backend engineering team to architect distributed database services, implement high-performance restful endpoints, and manage cloud deployments with docker and kubernetes.",
        "required_skills": ["python", "django", "postgresql", "rest api", "docker"],
        "preferred_skills": ["kubernetes", "aws", "microservices", "redis"],
        "experience_required": "3-5 years",
        "education_required": "bachelor's degree in engineering or software systems",
        "job_type": "full-time"
    },
    {
        "title": "full stack developer",
        "company": "nexus digital labs",
        "location": "new york, ny",
        "description": "looking for a versatile full stack engineer proficient in react, node.js, python, and modern web application development. you will collaborate across frontend ui and backend service layers.",
        "required_skills": ["javascript", "react", "python", "html5", "css3", "mysql"],
        "preferred_skills": ["typescript", "tailwind css", "next.js", "docker"],
        "experience_required": "2-4 years",
        "education_required": "bachelor's degree in computer science or equivalent",
        "job_type": "full-time"
    },
    {
        "title": "machine learning engineer",
        "company": "cognition ai labs",
        "location": "san francisco, ca",
        "description": "design, train, and deploy advanced machine learning and deep learning models into production. experience with pytorch, transformers, nlp, and model serving is highly valued.",
        "required_skills": ["python", "machine learning", "pytorch", "deep learning", "nlp", "scikit-learn"],
        "preferred_skills": ["huggingface", "llm", "docker", "aws", "pandas"],
        "experience_required": "3+ years",
        "education_required": "master's degree or bachelor's in ai, data science, or cs",
        "job_type": "full-time"
    },
    {
        "title": "data analyst",
        "company": "metricpulse intelligence",
        "location": "chicago, il",
        "description": "empower executive decision-making through rigorous data analysis, sql querying, etl pipelines, and interactive dashboards using power bi and tableau.",
        "required_skills": ["sql", "python", "data analysis", "tableau", "excel", "power bi"],
        "preferred_skills": ["pandas", "bigquery", "etl", "statistics"],
        "experience_required": "1-3 years",
        "education_required": "bachelor's degree in statistics, business analytics, or cs",
        "job_type": "full-time"
    },
    {
        "title": "software engineer",
        "company": "syntropy software",
        "location": "seattle, wa",
        "description": "develop scalable software architectures, maintain enterprise backends, and drive test-driven development methodologies across agile sprint cycles.",
        "required_skills": ["python", "java", "sql", "git", "rest api", "problem solving"],
        "preferred_skills": ["docker", "ci/cd", "linux", "unit testing"],
        "experience_required": "2-5 years",
        "education_required": "bachelor's degree in computer science",
        "job_type": "full-time"
    },
    {
        "title": "ai engineer",
        "company": "hyperion intelligence",
        "location": "remote",
        "description": "build next-generation generative ai applications, rag pipelines, and vector search integrations utilizing large language models and langchain.",
        "required_skills": ["python", "artificial intelligence", "llm", "langchain", "transformers", "rest api"],
        "preferred_skills": ["vector databases", "fastapi", "docker", "prompt engineering"],
        "experience_required": "2-4 years",
        "education_required": "bachelor's or master's in computer science or ai",
        "job_type": "full-time"
    },
    {
        "title": "data scientist",
        "company": "vanguard data",
        "location": "boston, ma",
        "description": "apply statistical modeling, predictive algorithms, and exploratory data analysis to complex enterprise datasets to extract actionable insights.",
        "required_skills": ["python", "data science", "scikit-learn", "pandas", "numpy", "sql"],
        "preferred_skills": ["data visualization", "deep learning", "spark", "r"],
        "experience_required": "2-4 years",
        "education_required": "master's degree or bachelor's in quantitative discipline",
        "job_type": "full-time"
    },
    {
        "title": "devops engineer",
        "company": "stratus cloudworks",
        "location": "denver, co",
        "description": "build, automate, and monitor reliable ci/cd pipelines, cloud infrastructure as code, and container orchestration clusters on aws and kubernetes.",
        "required_skills": ["docker", "kubernetes", "aws", "terraform", "ci/cd", "linux"],
        "preferred_skills": ["ansible", "prometheus", "grafana", "bash", "python"],
        "experience_required": "3-6 years",
        "education_required": "bachelor's degree in computer engineering or related",
        "job_type": "full-time"
    },
    {
        "title": "frontend developer",
        "company": "lumina interface studio",
        "location": "remote",
        "description": "craft performant, accessible, and visually stunning web interfaces with modern react, css3 animations, and responsive design systems.",
        "required_skills": ["javascript", "react", "html5", "css3", "responsive design", "git"],
        "preferred_skills": ["typescript", "tailwind css", "figma", "rest api"],
        "experience_required": "2-4 years",
        "education_required": "bachelor's degree or equivalent practical experience",
        "job_type": "full-time"
    },
    {
        "title": "cloud solutions architect",
        "company": "orbit cloud consulting",
        "location": "atlanta, ga",
        "description": "architect resilient multi-region cloud infrastructures, migration frameworks, and enterprise security policies across amazon web services and azure.",
        "required_skills": ["aws", "azure", "cloud", "docker", "linux", "networking"],
        "preferred_skills": ["terraform", "kubernetes", "python", "microservices"],
        "experience_required": "5+ years",
        "education_required": "bachelor's or master's degree in computer science",
        "job_type": "full-time"
    },
    {
        "title": "data engineer",
        "company": "streamline data platforms",
        "location": "remote",
        "description": "construct high-throughput etl pipelines, manage data lakes, and optimize big data query processing engines with spark, airflow, and mysql.",
        "required_skills": ["python", "sql", "data engineering", "etl", "spark", "airflow"],
        "preferred_skills": ["snowflake", "kafka", "docker", "aws"],
        "experience_required": "3-5 years",
        "education_required": "bachelor's degree in computer science or data engineering",
        "job_type": "full-time"
    }
]

def init_database():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

        for cat, skills in SKILL_TAXONOMY.items():
            for sk in skills:
                norm_name = normalize_skill(sk)
                existing = Skill.query.filter_by(name=norm_name).first()
                if not existing:
                    new_skill = Skill(name=norm_name, category=cat.lower())
                    db.session.add(new_skill)
        db.session.commit()

        for j_data in SAMPLE_JOBS:
            existing_job = Job.query.filter_by(title=j_data["title"], company=j_data["company"]).first()
            if not existing_job:
                job = Job(
                    title=j_data["title"],
                    company=j_data["company"],
                    location=j_data["location"],
                    description=j_data["description"],
                    experience_required=j_data["experience_required"],
                    education_required=j_data["education_required"],
                    job_type=j_data["job_type"]
                )
                job.set_required_skills(j_data["required_skills"])
                job.set_preferred_skills(j_data["preferred_skills"])
                db.session.add(job)
        db.session.commit()

        test_user = User.query.filter_by(email="demo@jobalign.ai").first()
        if not test_user:
            demo_user = User(
                name="alex rivera",
                email="demo@jobalign.ai",
                location="san francisco, ca",
                linkedin="https://linkedin.com/in/alexrivera-demo",
                github="https://github.com/alexrivera-demo",
                portfolio="https://alexrivera.dev",
                career_interests="backend development, machine learning, ai systems"
            )
            demo_user.set_password("password123")
            db.session.add(demo_user)
            db.session.commit()

            sample_resume_text = (
                "alex rivera\n"
                "alex.rivera@example.com | (555) 234-5678 | san francisco, ca\n"
                "linkedin: linkedin.com/in/alexrivera-demo | github: github.com/alexrivera-demo | portfolio: alexrivera.dev\n\n"
                "professional summary\n"
                "results-driven software engineer with 3+ years of experience designing and deploying scalable backend systems, rest apis, and machine learning pipelines. proficient in python, flask, mysql, docker, and cloud environments.\n\n"
                "technical skills\n"
                "programming languages: python, javascript, sql, c++\n"
                "frameworks: flask, fastapi, django, react, scikit-learn, pytorch\n"
                "databases: mysql, postgresql, redis\n"
                "cloud & devops: docker, git, github actions, linux, ci/cd\n"
                "ai/ml: machine learning, natural language processing, deep learning, pandas, numpy\n"
                "soft skills: problem solving, agile, collaboration, communication\n\n"
                "work experience\n"
                "backend software engineer at novatech solutions (2022 - present)\n"
                "- designed and built high-performance microservices using python and flask handling 2m+ daily requests.\n"
                "- optimized mysql database queries and indexing strategies, reducing endpoint response times by 38%.\n"
                "- implemented restful api endpoints with jwt authentication and role-based permissions.\n"
                "- containerized backend services using docker and established github actions ci/cd pipelines.\n\n"
                "junior software developer at datamind labs (2021 - 2022)\n"
                "- developed automated data ingestion scripts and data pipelines using python and pandas.\n"
                "- collaborated with cross-functional product teams in agile sprint planning and code reviews.\n"
                "- integrated postgresql databases with internal web dashboards.\n\n"
                "education\n"
                "bachelor of science in computer science\n"
                "university of california, berkeley (2017 - 2021)\n"
                "gpa: 3.8 / 4.0\n\n"
                "projects\n"
                "ai resume analyzer\n"
                "developed an nlp-powered document evaluation tool utilizing python, flask, and semantic text embeddings.\n"
                "distributed task queue\n"
                "engineered an asynchronous job execution framework using redis, python, and mysql for background processing.\n\n"
                "certifications\n"
                "aws certified cloud practitioner\n"
                "python for data science and machine learning bootcamp"
            )

            from services.resume_parser import parse_resume_content
            parsed = parse_resume_content(sample_resume_text)
            
            sample_resume = Resume(
                user_id=demo_user.id,
                filename="alex_rivera_resume.txt",
                extracted_text=sample_resume_text
            )
            sample_resume.set_parsed_data(parsed)
            db.session.add(sample_resume)
            db.session.commit()

            python_job = Job.query.filter_by(title="python developer").first()
            if python_job:
                from services.matching_engine import match_resume_to_job
                match_res = match_resume_to_job(
                    parsed,
                    {
                        "title": python_job.title,
                        "company": python_job.company,
                        "location": python_job.location,
                        "required_skills": python_job.get_required_skills(),
                        "preferred_skills": python_job.get_preferred_skills(),
                        "experience": python_job.experience_required,
                        "education": python_job.education_required,
                        "description": python_job.description
                    },
                    raw_resume_text=sample_resume_text,
                    raw_job_text=python_job.description
                )
                
                initial_match = Match(
                    user_id=demo_user.id,
                    resume_id=sample_resume.id,
                    job_id=python_job.id,
                    job_title=python_job.title,
                    company_name=python_job.company,
                    overall_score=match_res["overall_score"],
                    skill_score=match_res["breakdown"]["skill_score"],
                    experience_score=match_res["breakdown"]["experience_score"],
                    semantic_score=match_res["breakdown"]["semantic_score"],
                    education_score=match_res["breakdown"]["education_score"],
                    project_score=match_res["breakdown"]["project_score"]
                )
                initial_match.set_matched_skills(match_res["matched_skills"])
                initial_match.set_missing_skills(match_res["missing_skills"])
                initial_match.set_partial_skills(match_res["partial_skills"])
                initial_match.set_explanation(match_res["explanation"])
                initial_match.set_recommendations(match_res["recommendations"])
                db.session.add(initial_match)
                db.session.commit()

if __name__ == "__main__":
    init_database()
