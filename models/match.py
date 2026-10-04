import json
from datetime import datetime, timezone
from models import db

class Match(db.Model):
    __tablename__ = "ss_matches"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("ss_users.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("ss_resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("ss_jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    job_title = db.Column(db.String(200), nullable=True)
    company_name = db.Column(db.String(200), nullable=True)
    overall_score = db.Column(db.Float, nullable=False, default=0.0)
    skill_score = db.Column(db.Float, nullable=False, default=0.0)
    experience_score = db.Column(db.Float, nullable=False, default=0.0)
    semantic_score = db.Column(db.Float, nullable=False, default=0.0)
    education_score = db.Column(db.Float, nullable=False, default=0.0)
    project_score = db.Column(db.Float, nullable=False, default=0.0)
    matched_skills = db.Column(db.Text, nullable=False, default="[]")
    missing_skills = db.Column(db.Text, nullable=False, default="[]")
    partial_skills = db.Column(db.Text, nullable=False, default="[]")
    explanation = db.Column(db.Text, nullable=False, default="{}")
    recommendations = db.Column(db.Text, nullable=False, default="[]")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def get_matched_skills(self):
        try:
            return json.loads(self.matched_skills)
        except Exception:
            return []

    def set_matched_skills(self, skills):
        self.matched_skills = json.dumps(skills)

    def get_missing_skills(self):
        try:
            return json.loads(self.missing_skills)
        except Exception:
            return []

    def set_missing_skills(self, skills):
        self.missing_skills = json.dumps(skills)

    def get_partial_skills(self):
        try:
            return json.loads(self.partial_skills)
        except Exception:
            return []

    def set_partial_skills(self, skills):
        self.partial_skills = json.dumps(skills)

    def get_explanation(self):
        try:
            return json.loads(self.explanation)
        except Exception:
            return {}

    def set_explanation(self, expl):
        self.explanation = json.dumps(expl)

    def get_recommendations(self):
        try:
            return json.loads(self.recommendations)
        except Exception:
            return []

    def set_recommendations(self, recs):
        self.recommendations = json.dumps(recs)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "resume_id": self.resume_id,
            "job_id": self.job_id,
            "job_title": self.job_title.lower() if self.job_title else "",
            "company_name": self.company_name.lower() if self.company_name else "",
            "overall_score": round(self.overall_score, 1),
            "skill_score": round(self.skill_score, 1),
            "experience_score": round(self.experience_score, 1),
            "semantic_score": round(self.semantic_score, 1),
            "education_score": round(self.education_score, 1),
            "project_score": round(self.project_score, 1),
            "matched_skills": self.get_matched_skills(),
            "missing_skills": self.get_missing_skills(),
            "partial_skills": self.get_partial_skills(),
            "explanation": self.get_explanation(),
            "recommendations": self.get_recommendations(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
