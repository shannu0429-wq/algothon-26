import json
from datetime import datetime, timezone
from models import db

class Resume(db.Model):
    __tablename__ = "ss_resumes"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("ss_users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text(length=4294967295), nullable=False)
    parsed_data = db.Column(db.Text(length=4294967295), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    matches = db.relationship("Match", backref="resume", lazy=True, cascade="all, delete-orphan")

    def get_parsed_data(self):
        try:
            return json.loads(self.parsed_data)
        except Exception:
            return {}

    def set_parsed_data(self, data):
        self.parsed_data = json.dumps(data)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "extracted_text": self.extracted_text,
            "parsed_data": self.get_parsed_data(),
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }
