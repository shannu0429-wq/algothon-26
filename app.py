import os
from flask import Flask, render_template, session, jsonify
from config import Config
from models import db, User, Resume, Job, Match
from routes import auth_bp, dashboard_bp, resume_bp, job_bp, matching_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["RESUME_UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["JOB_UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(matching_bp)

    @app.context_processor
    def inject_global_data():
        user = None
        has_resume = False
        if "user_id" in session:
            user = db.session.get(User, session["user_id"])
            if user:
                res_count = Resume.query.filter_by(user_id=user.id).count()
                has_resume = res_count > 0
        return {
            "current_user": user,
            "has_resume": has_resume,
            "app_name": "jobalign ai",
            "app_tagline": "match your skills. find your future."
        }

    @app.route("/")
    def index():
        jobs_count = Job.query.count()
        featured_jobs = Job.query.limit(4).all()
        return render_template(
            "index.html",
            jobs_count=jobs_count,
            featured_jobs=[j.to_dict() for j in featured_jobs]
        )

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
