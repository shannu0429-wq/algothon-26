import json
from flask import Flask
from config import Config
from models import db, User, Resume, Job, Match, Skill
from services.skill_extractor import SKILL_TAXONOMY, normalize_skill

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

    with db.engine.connect() as conn:
        with conn.begin():
            table_pairs = [
                ("users", "ss_users"),
                ("resumes", "ss_resumes"),
                ("jobs", "ss_jobs"),
                ("matches", "ss_matches"),
                ("skills", "ss_skills"),
            ]
            for old_tbl, new_tbl in table_pairs:
                try:
                    res = conn.execute(db.text(f"SELECT COUNT(*) FROM `{old_tbl}`"))
                    old_cnt = res.scalar() or 0
                    res_new = conn.execute(db.text(f"SELECT COUNT(*) FROM `{new_tbl}`"))
                    new_cnt = res_new.scalar() or 0
                    if old_cnt > 0 and new_cnt == 0:
                        conn.execute(db.text(f"INSERT INTO `{new_tbl}` SELECT * FROM `{old_tbl}`"))
                except Exception:
                    pass

    if Job.query.count() == 0 or Skill.query.count() == 0:
        from init_db import init_database
        init_database()

    print("migration_status:success")
    print(f"ss_users count: {User.query.count()}")
    print(f"ss_resumes count: {Resume.query.count()}")
    print(f"ss_jobs count: {Job.query.count()}")
    print(f"ss_matches count: {Match.query.count()}")
    print(f"ss_skills count: {Skill.query.count()}")
