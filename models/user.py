from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model):
    __tablename__ = "ss_users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(191), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(150), nullable=True, default="")
    linkedin = db.Column(db.String(255), nullable=True, default="")
    github = db.Column(db.String(255), nullable=True, default="")
    portfolio = db.Column(db.String(255), nullable=True, default="")
    career_interests = db.Column(db.String(255), nullable=True, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    resumes = db.relationship("Resume", backref="user", lazy=True, cascade="all, delete-orphan")
    matches = db.relationship("Match", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name.lower() if self.name else "",
            "email": self.email.lower() if self.email else "",
            "location": self.location.lower() if self.location else "",
            "linkedin": self.linkedin.lower() if self.linkedin else "",
            "github": self.github.lower() if self.github else "",
            "portfolio": self.portfolio.lower() if self.portfolio else "",
            "career_interests": self.career_interests.lower() if self.career_interests else "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
