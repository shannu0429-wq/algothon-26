import unittest
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from config import Config
from models import db, User, Resume, Job, Match, Skill
from services.skill_extractor import extract_skills, normalize_skill
from services.resume_parser import parse_resume_content
from services.job_parser import parse_job_description
from services.embedding_service import compute_semantic_similarity
from services.matching_engine import match_resume_to_job
from services.ranking_engine import rank_jobs_for_resume

class JobAlignAITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False
        cls.client = cls.app.test_client()

    def test_01_skill_extractor_normalization(self):
        self.assertEqual(normalize_skill("js"), "javascript")
        self.assertEqual(normalize_skill("ml"), "machine learning")
        self.assertEqual(normalize_skill("nlp"), "natural language processing")
        self.assertEqual(normalize_skill("k8s"), "kubernetes")

        messy_text = "skills: python, js, ml, restful apis, docker, k8s, sql, aws"
        extracted = extract_skills(messy_text)
        self.assertIn("python", extracted["all_skills"])
        self.assertIn("javascript", extracted["all_skills"])
        self.assertIn("machine learning", extracted["all_skills"])
        self.assertIn("rest api", extracted["all_skills"])
        self.assertIn("docker", extracted["all_skills"])
        self.assertIn("kubernetes", extracted["all_skills"])
        self.assertIn("sql", extracted["all_skills"])

    def test_02_messy_resume_parsing(self):
        messy_resume = (
            "   JANE   DOE   \n"
            "jane.doe@techdomain.org | (555) 987-6543 | New York, NY\n"
            "github.com/janedoe-dev | linkedin.com/in/janedoe-dev\n\n"
            "=== PROFESSIONAL SUMMARY ===\n"
            "backend developer with 4 years building high scale APIs with python, flask, and mysql.\n\n"
            "*** TECHNICAL SKILLS ***\n"
            "python, flask, fastapi, mysql, redis, docker, git, rest api\n\n"
            "--- EMPLOYMENT HISTORY ---\n"
            "senior backend developer at fintech cloud corp (2022 - present)\n"
            "• engineered rest api services using python and flask.\n"
            "• optimized mysql database queries and database indexing.\n\n"
            "=== ACADEMIC BACKGROUND ===\n"
            "bachelor of science in computer science, columbia university (2018 - 2022)\n"
            "gpa: 3.9 / 4.0\n\n"
            "*** PROJECTS ***\n"
            "distributed cache manager\n"
            "built cache invalidation protocol using redis and python.\n\n"
            "*** CERTIFICATES ***\n"
            "aws certified solutions architect"
        )
        parsed = parse_resume_content(messy_resume)
        self.assertEqual(parsed["personal_info"]["name"], "jane doe")
        self.assertEqual(parsed["personal_info"]["email"], "jane.doe@techdomain.org")
        self.assertIn("python", parsed["skills"])
        self.assertIn("flask", parsed["skills"])
        self.assertIn("mysql", parsed["skills"])
        self.assertTrue(len(parsed["education"]) > 0)
        self.assertTrue(len(parsed["experience"]) > 0)
        self.assertTrue(len(parsed["projects"]) > 0)
        self.assertTrue(len(parsed["certifications"]) > 0)

    def test_03_job_parser(self):
        sample_jd = (
            "job title: python engineer\n"
            "company: datavault inc\n"
            "location: remote\n"
            "requirements:\n"
            "- 3+ years experience with python, flask, and mysql\n"
            "- hands-on with docker and rest api design\n\n"
            "nice to have:\n"
            "- experience with redis and aws cloud\n\n"
            "responsibilities:\n"
            "- develop and maintain clean backend services\n"
            "- collaborate with frontend engineers"
        )
        parsed_job = parse_job_description(sample_jd)
        self.assertEqual(parsed_job["title"], "python engineer")
        self.assertEqual(parsed_job["company"], "datavault inc")
        self.assertIn("python", parsed_job["required_skills"])
        self.assertIn("flask", parsed_job["required_skills"])
        self.assertIn("mysql", parsed_job["required_skills"])

    def test_04_matching_engine_and_scoring(self):
        resume_data = {
            "skills": ["python", "flask", "mysql", "rest api", "docker"],
            "skills_by_category": {
                "programming languages": ["python"],
                "frameworks": ["flask"],
                "databases": ["mysql"]
            },
            "experience": [{
                "title": "software engineer",
                "company": "tech corp",
                "duration": "2022 - present",
                "responsibilities": ["developed apis"],
                "technologies": ["python", "flask"]
            }],
            "education": [{
                "degree": "bachelor of science",
                "institution": "university",
                "field": "computer science",
                "graduation_year": "2022"
            }],
            "projects": [{
                "name": "api service",
                "description": "python and flask microservice",
                "technologies": ["python", "flask"]
            }]
        }

        job_data = {
            "title": "python developer",
            "company": "apex analytics",
            "location": "remote",
            "required_skills": ["python", "flask", "mysql", "rest api"],
            "preferred_skills": ["aws", "docker"],
            "experience": "2-4 years",
            "education": "bachelor's degree",
            "description": "seeking python developer with flask, mysql, docker, and aws."
        }

        result = match_resume_to_job(resume_data, job_data)
        self.assertGreaterEqual(result["overall_score"], 60.0)
        self.assertIn(result["category"], ["good match", "strong match", "excellent match"])
        self.assertIn("python", result["matched_skills"])
        self.assertIn("flask", result["matched_skills"])
        self.assertIn("aws", result["missing_skills"])
        self.assertTrue(len(result["recommendations"]) > 0)
        self.assertIn("technical_alignment", result["explanation"])

    def test_05_auth_and_protected_routes(self):
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

        reg_data = {
            "name": "tester user",
            "email": "test_auto@jobalign.ai",
            "password": "testpassword123",
            "confirm_password": "testpassword123"
        }
        with self.app.app_context():
            existing = User.query.filter_by(email="test_auto@jobalign.ai").first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

        res_reg = self.client.post("/register", data=reg_data, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)

        res_dash = self.client.get("/dashboard")
        self.assertEqual(res_dash.status_code, 200)

        res_jobs = self.client.get("/jobs")
        self.assertEqual(res_jobs.status_code, 200)

        res_logout = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)

    def test_06_demo_match_endpoint(self):
        res = self.client.post("/api/demo-match")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("match_id", data)
        self.assertIn("redirect_url", data)

    def test_07_job_ranking(self):
        with self.app.app_context():
            jobs = Job.query.limit(4).all()
            dummy_resume = {
                "skills": ["python", "flask", "mysql", "rest api"],
                "experience": [{"duration": "2021 - 2024"}],
                "education": [{"degree": "bachelor"}],
                "projects": [{"name": "app", "description": "python web app"}]
            }
            ranked = rank_jobs_for_resume(dummy_resume, "python flask developer with mysql", jobs)
            self.assertEqual(len(ranked), len(jobs))
            self.assertGreaterEqual(ranked[0]["match_score"], ranked[-1]["match_score"])

if __name__ == "__main__":
    unittest.main()
