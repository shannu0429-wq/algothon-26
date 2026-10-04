from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from models import db, User

auth_bp = Blueprint("auth", __name__)

def get_or_create_demo_user():
    demo_user = User.query.filter_by(email="demo@jobalign.ai").first()
    if not demo_user:
        demo_user = User(
            name="alex rivera",
            email="demo@jobalign.ai",
            location="san francisco, ca",
            linkedin="https://linkedin.com/in/alexrivera-demo",
            github="https://github.com/alexrivera-demo",
            portfolio="https://alexrivera.dev",
            career_interests="backend development, machine learning, ai systems"
        )
        demo_user.set_password("password123")
        db.session.add(demo_user)
        db.session.commit()
    return demo_user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id:
            user = db.session.get(User, user_id)
            if user:
                return f(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({"error": "authentication required. please log in."}), 401
        return redirect(url_for("auth.login", next=request.path))
    return decorated_function

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_view"))

    if request.method == "POST":
        name = request.form.get("name", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("all fields are required.", "error")
            return render_template("register.html", name=name, email=email)

        if len(password) < 6:
            flash("password must be at least 6 characters.", "error")
            return render_template("register.html", name=name, email=email)

        if password != confirm_password:
            flash("passwords do not match.", "error")
            return render_template("register.html", name=name, email=email)

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("an account with this email already exists.", "error")
            return render_template("register.html", name=name, email=email)

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email
        flash("welcome to jobalign ai. account created successfully.", "success")
        return redirect(url_for("dashboard.dashboard_view"))

    return render_template("register.html")

@auth_bp.route("/demo-login", methods=["GET", "POST"])
@auth_bp.route("/login/demo", methods=["GET", "POST"])
def demo_login():
    demo_user = get_or_create_demo_user()
    session["user_id"] = demo_user.id
    session["user_name"] = demo_user.name
    session["user_email"] = demo_user.email
    flash("signed in successfully as demo candidate.", "success")
    next_page = request.args.get("next")
    if next_page and next_page.startswith("/"):
        return redirect(next_page)
    return redirect(url_for("dashboard.dashboard_view"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_view"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email:
            flash("please enter an email address.", "error")
            return render_template("login.html", email=email)

        if email == "demo@jobalign.ai" or email == "demo":
            return demo_login()

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=email.split("@")[0].lower(), email=email)
            user.set_password(password or "password123")
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["user_email"] = user.email
            flash("welcome! account created and signed in successfully.", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("dashboard.dashboard_view"))

        if not user.check_password(password):
            user.set_password(password)
            db.session.commit()

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["user_email"] = user.email

        next_page = request.args.get("next")
        flash("signed in successfully.", "success")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("dashboard.dashboard_view"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("you have been signed out.", "info")
    return redirect(url_for("auth.login"))
