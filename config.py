import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("flask_secret_key", "jobalign_ai_secret_key_default_2026")
    MYSQL_HOST = os.getenv("mysql_host", "localhost")
    MYSQL_PORT = int(os.getenv("mysql_port", 3306))
    MYSQL_USER = os.getenv("mysql_user", "root")
    MYSQL_PASSWORD = os.getenv("mysql_password", "admin")
    MYSQL_DATABASE = os.getenv("mysql_database", "jobalign_ai")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    RESUME_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "resumes")
    JOB_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "job_descriptions")
    MAX_CONTENT_LENGTH = int(os.getenv("max_content_length", 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "png", "jpg", "jpeg"}
