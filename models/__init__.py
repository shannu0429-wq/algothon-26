from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.resume import Resume
from models.job import Job
from models.match import Match
from models.skill import Skill
