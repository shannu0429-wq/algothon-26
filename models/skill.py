from models import db

class Skill(db.Model):
    __tablename__ = "ss_skills"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name.lower(),
            "category": self.category.lower(),
        }
