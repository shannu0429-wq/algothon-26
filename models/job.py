import json
from datetime import datetime, timezone
from models import db

class Job(db.Model):
    __tablename__ = "ss_jobs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    company = db.Column(db.String(200), nullable=False, index=True)
    location = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text(length=4294967295), nullable=False)
    required_skills = db.Column(db.Text, nullable=False, default="[]")
    preferred_skills = db.Column(db.Text, nullable=False, default="[]")
    experience_required = db.Column(db.String(100), nullable=False, default="0-1 years")
    education_required = db.Column(db.String(150), nullable=False, default="bachelor's degree")
    job_type = db.Column(db.String(50), nullable=False, default="full-time")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    matches = db.relationship("Match", backref="job", lazy=True, cascade="all, delete-orphan")

    def get_required_skills(self):
        try:
            return json.loads(self.required_skills)
        except Exception:
            return []

    def set_required_skills(self, skills):
        self.required_skills = json.dumps(skills)

    def get_preferred_skills(self):
        try:
            return json.loads(self.preferred_skills)
        except Exception:
            return []

    def set_preferred_skills(self, skills):
        self.preferred_skills = json.dumps(skills)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title.lower() if self.title else "",
            "company": self.company.lower() if self.company else "",
            "location": self.location.lower() if self.location else "",
            "description": self.description,
            "required_skills": self.get_required_skills(),
            "preferred_skills": self.get_preferred_skills(),
            "experience_required": self.experience_required.lower() if self.experience_required else "",
            "education_required": self.education_required.lower() if self.education_required else "",
            "job_type": self.job_type.lower() if self.job_type else "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
