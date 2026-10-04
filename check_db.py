import os
import sys
import json
import pymysql
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("mysql_host", "localhost")
MYSQL_PORT = int(os.getenv("mysql_port", 3306))
MYSQL_USER = os.getenv("mysql_user", "root")
MYSQL_PASSWORD = os.getenv("mysql_password", "admin")
MYSQL_DATABASE = os.getenv("mysql_database", "jobalign_ai")

def format_row(values, widths):
    return " | ".join(str(v).ljust(w) for v, w in zip(values, widths))

def print_separator(widths):
    print("-+-".join("-" * w for w in widths))

def check_database():
    print("=" * 70)
    print("jobalign ai — mysql database inspection tool")
    print("=" * 70)
    print(f"host:     {MYSQL_HOST}:{MYSQL_PORT}")
    print(f"user:     {MYSQL_USER}")
    print(f"database: {MYSQL_DATABASE}")
    print("-" * 70)

    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        print("connection status: success (connected to mysql)")
    except Exception as exc:
        print(f"connection status: failed ({str(exc).lower()})")
        sys.exit(1)

    with conn.cursor() as cursor:
        cursor.execute("select version() as ver;")
        ver = cursor.fetchone()
        print(f"mysql version:     {ver['ver']}")
        print("-" * 70)

        cursor.execute("show tables;")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        print(f"tables found ({len(tables)}): {', '.join(tables)}")
        print("=" * 70)

        target_tables = ["ss_users", "ss_resumes", "ss_jobs", "ss_matches", "ss_skills"]
        for tbl in target_tables:
            if tbl in tables:
                cursor.execute(f"select count(*) as total from `{tbl}`;")
                count = cursor.fetchone()["total"]
                print(f"table `{tbl}`: {count} total rows")
            else:
                print(f"table `{tbl}`: not created yet")

        print("=" * 70)
        print("table: ss_users (sample records)")
        if "ss_users" in tables:
            cursor.execute("select id, name, email, location, created_at from ss_users limit 10;")
            users = cursor.fetchall()
            if users:
                widths = [4, 20, 26, 18, 20]
                print(format_row(["id", "name", "email", "location", "created_at"], widths))
                print_separator(widths)
                for u in users:
                    dt_str = str(u["created_at"])[:19] if u["created_at"] else ""
                    print(format_row([u["id"], u["name"] or "", u["email"] or "", u["location"] or "", dt_str], widths))
            else:
                print("no user records found in ss_users.")
        else:
            users = []
            print("table ss_users does not exist.")

        print("=" * 70)
        print("table: ss_resumes (sample records)")
        if "ss_resumes" in tables:
            cursor.execute("select id, user_id, filename, uploaded_at, parsed_data from ss_resumes limit 10;")
            resumes = cursor.fetchall()
            if resumes:
                widths = [4, 8, 24, 20, 16]
                print(format_row(["id", "user_id", "filename", "uploaded_at", "skills count"], widths))
                print_separator(widths)
                for r in resumes:
                    skills_cnt = 0
                    try:
                        p = json.loads(r["parsed_data"])
                        skills_cnt = len(p.get("skills", []))
                    except Exception:
                        pass
                    dt_str = str(r["uploaded_at"])[:19] if r["uploaded_at"] else ""
                    print(format_row([r["id"], r["user_id"], r["filename"][:24], dt_str, f"{skills_cnt} skills"], widths))
            else:
                print("no resume records found in ss_resumes.")
        else:
            resumes = []
            print("table ss_resumes does not exist.")

        print("=" * 70)
        print("table: ss_jobs (sample records)")
        if "ss_jobs" in tables:
            cursor.execute("select id, title, company, location, experience_required, job_type from ss_jobs limit 10;")
            jobs = cursor.fetchall()
            if jobs:
                widths = [4, 26, 22, 16, 14, 12]
                print(format_row(["id", "title", "company", "location", "experience", "type"], widths))
                print_separator(widths)
                for j in jobs:
                    print(format_row([j["id"], j["title"][:26], j["company"][:22], j["location"][:16], j["experience_required"][:14], j["job_type"]], widths))
            else:
                print("no job records found in ss_jobs.")
        else:
            jobs = []
            print("table ss_jobs does not exist.")

        print("=" * 70)
        print("table: ss_matches (sample records)")
        if "ss_matches" in tables:
            cursor.execute("select id, user_id, job_title, company_name, overall_score, created_at from ss_matches limit 10;")
            matches = cursor.fetchall()
            if matches:
                widths = [4, 8, 26, 22, 12, 20]
                print(format_row(["id", "user_id", "job title", "company", "score", "created_at"], widths))
                print_separator(widths)
                for m in matches:
                    dt_str = str(m["created_at"])[:19] if m["created_at"] else ""
                    print(format_row([m["id"], m["user_id"], (m["job_title"] or "")[:26], (m["company_name"] or "")[:22], f"{m['overall_score']}%", dt_str], widths))
            else:
                print("no match records found in ss_matches.")
        else:
            matches = []
            print("table ss_matches does not exist.")

        print("=" * 70)
        print("table: ss_skills (taxonomy category distribution)")
        if "ss_skills" in tables:
            cursor.execute("select category, count(*) as count from ss_skills group by category order by count desc;")
            cats = cursor.fetchall()
            if cats:
                widths = [26, 8]
                print(format_row(["category", "skills count"], widths))
                print_separator(widths)
                for c in cats:
                    print(format_row([c["category"], c["count"]], widths))
        else:
            print("table ss_skills does not exist.")

        print("=" * 70)
        print("summary verification:")
        ss_present = [tbl for tbl in target_tables if tbl in tables]
        all_ok = len(ss_present) == 5 and len(users) >= 1 and len(jobs) >= 1
        if all_ok:
            print("all ss_ tables and seed records are active, healthy, and accessible.")
        else:
            print(f"{len(ss_present)}/5 ss_ tables found. run `python init_db.py` to create and populate.")
        print("=" * 70)

    conn.close()

if __name__ == "__main__":
    check_database()
