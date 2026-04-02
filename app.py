"""
NeuroMATCH AI — Full Stack Application
Uses SQLite (built into Python — zero installation needed!)
Phases 1–7: Auth + Resume Parser + Job Portal + HR Dashboard + Ranking + AI
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3, os, json

from nlp.resume_parser import parse_resume
from nlp.scorer        import score_resume
from nlp.job_matcher   import match_resume_to_job, recommend_jobs
from nlp.ai_features   import generate_interview_questions, generate_email

# ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "neuromatch-secret-key-change-in-production"

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DB_PATH      = os.path.join(BASE_DIR, "neuromatch.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXT = {"pdf", "docx"}

# ──────────────────────────────────────────────────────────────────
# DATABASE HELPERS
# ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # dict-like rows
    conn.execute("PRAGMA journal_mode=WAL") # safe concurrent writes
    return conn

def init_db():
    """Create all tables + seed sample jobs on first run."""
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        email      TEXT NOT NULL UNIQUE,
        password   TEXT NOT NULL,
        phone      TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS companies (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        hr_name      TEXT NOT NULL,
        email        TEXT NOT NULL UNIQUE,
        password     TEXT NOT NULL,
        industry     TEXT DEFAULT '',
        created_at   TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS resumes (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER NOT NULL,
        filename     TEXT NOT NULL,
        skills       TEXT DEFAULT '[]',
        education    TEXT DEFAULT '',
        experience   TEXT DEFAULT '',
        score        REAL DEFAULT 0,
        keywords_json TEXT DEFAULT '{}',
        uploaded_at  TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id       INTEGER,
        title            TEXT NOT NULL,
        location         TEXT DEFAULT '',
        domain           TEXT DEFAULT '',
        skills_required  TEXT DEFAULT '',
        description      TEXT DEFAULT '',
        salary           TEXT DEFAULT '',
        job_type         TEXT DEFAULT 'Full-time',
        posted_at        TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS candidates (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL,
        company_id  INTEGER NOT NULL,
        job_id      INTEGER,
        filename    TEXT DEFAULT '',
        score       REAL DEFAULT 0,
        match_pct   REAL DEFAULT 0,
        skills_json TEXT DEFAULT '[]',
        strengths   TEXT DEFAULT '[]',
        weaknesses  TEXT DEFAULT '[]',
        hidden_gems TEXT DEFAULT '[]',
        status      TEXT DEFAULT 'pending',
        hr_comment  TEXT DEFAULT '',
        screened_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (user_id)    REFERENCES users(id),
        FOREIGN KEY (company_id) REFERENCES companies(id)
    );
    """)

    # Seed sample jobs only if empty
    count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if count == 0:
        sample_jobs = [
            (None,"Python Developer Intern","Bangalore","Technology",
             "Python, Flask, SQL, REST API, Git",
             "Build backend services and REST APIs. Work with a fast-paced startup team.",
             "15,000–20,000/month","Internship"),
            (None,"Data Science Intern","Remote","Data Science",
             "Python, Pandas, Scikit-learn, Machine Learning, SQL, Matplotlib",
             "Analyse large datasets, build ML models, create dashboards.",
             "18,000–25,000/month","Internship"),
            (None,"Frontend Developer Intern","Hyderabad","Technology",
             "HTML, CSS, JavaScript, React, Figma, UI/UX",
             "Design and implement responsive web interfaces.",
             "12,000–18,000/month","Internship"),
            (None,"ML Engineer","Pune","AI/ML",
             "TensorFlow, PyTorch, NLP, Deep Learning, Python, Docker",
             "Develop and deploy machine learning models for production.",
             "25,000–35,000/month","Full-time"),
            (None,"Business Analyst Intern","Mumbai","Business",
             "Excel, SQL, Power BI, Data Analysis, Communication, Presentation",
             "Support strategic decisions by analysing data and creating reports.",
             "10,000–15,000/month","Internship"),
            (None,"DevOps Engineer","Chennai","Infrastructure",
             "Docker, Kubernetes, AWS, CI/CD, Linux, Terraform",
             "Manage cloud infrastructure and automate deployments.",
             "30,000–45,000/month","Full-time"),
            (None,"UI/UX Designer Intern","Bangalore","Design",
             "Figma, Adobe XD, Wireframing, Prototyping, CSS",
             "Create user-centred designs for web and mobile apps.",
             "10,000–15,000/month","Internship"),
            (None,"Android Developer","Delhi","Mobile",
             "Kotlin, Java, Android SDK, Firebase, REST API, Git",
             "Develop and maintain Android applications for 1M+ users.",
             "20,000–30,000/month","Full-time"),
            (None,"Cybersecurity Intern","Remote","Security",
             "Networking, Linux, Python, Ethical Hacking, OWASP",
             "Assist in vulnerability assessments and security audits.",
             "12,000–18,000/month","Internship"),
            (None,"Full Stack Developer","Bangalore","Technology",
             "React, Node.js, Python, MongoDB, Docker, AWS",
             "End-to-end development of web applications.",
             "30,000–50,000/month","Full-time"),
        ]
        conn.executemany(
            "INSERT INTO jobs(company_id,title,location,domain,skills_required,"
            "description,salary,job_type) VALUES(?,?,?,?,?,?,?,?)",
            sample_jobs)

    conn.commit()
    conn.close()


def qd(conn, sql, args=(), one=False):
    """Query returning dict rows."""
    cur = conn.execute(sql, args)
    rows = cur.fetchall()
    result = [dict(r) for r in rows]
    return result[0] if (one and result) else (None if one else result)


def qw(conn, sql, args=()):
    """Write query, returns lastrowid."""
    cur = conn.execute(sql, args)
    conn.commit()
    return cur.lastrowid


def allowed(fname):
    return "." in fname and fname.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ──────────────────────────────────────────────────────────────────
# HOME
# ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ══════════════════════════════════════════════════════════════════
# PHASE 1 — USER (STUDENT) AUTH
# ══════════════════════════════════════════════════════════════════
@app.route("/user/register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        name  = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]
        phone = request.form.get("phone", "").strip()
        conn  = get_db()
        if qd(conn, "SELECT id FROM users WHERE email=?", (email,), one=True):
            flash("Email already registered. Please login.", "error")
        else:
            qw(conn, "INSERT INTO users(name,email,password,phone) VALUES(?,?,?,?)",
               (name, email, generate_password_hash(pwd), phone))
            flash("Account created! Please login.", "success")
            conn.close()
            return redirect(url_for("user_login"))
        conn.close()
    return render_template("user_register.html")


@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]
        conn  = get_db()
        u     = qd(conn, "SELECT * FROM users WHERE email=?", (email,), one=True)
        conn.close()
        if u and check_password_hash(u["password"], pwd):
            session.update({"user_id": u["id"], "user_name": u["name"], "role": "user"})
            return redirect(url_for("user_dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("user_login.html")


@app.route("/user/dashboard")
def user_dashboard():
    if session.get("role") != "user":
        return redirect(url_for("user_login"))
    conn    = get_db()
    resumes = qd(conn, "SELECT * FROM resumes WHERE user_id=? ORDER BY uploaded_at DESC",
                 (session["user_id"],))
    conn.close()
    return render_template("user_dashboard.html", name=session["user_name"], resumes=resumes)


# ══════════════════════════════════════════════════════════════════
# PHASE 1 — COMPANY (HR) AUTH
# ══════════════════════════════════════════════════════════════════
@app.route("/company/register", methods=["GET", "POST"])
def company_register():
    if request.method == "POST":
        cname    = request.form["company_name"].strip()
        hr_name  = request.form["hr_name"].strip()
        email    = request.form["email"].strip().lower()
        pwd      = request.form["password"]
        industry = request.form.get("industry", "")
        conn     = get_db()
        if qd(conn, "SELECT id FROM companies WHERE email=?", (email,), one=True):
            flash("Email already registered.", "error")
        else:
            qw(conn, "INSERT INTO companies(company_name,hr_name,email,password,industry) VALUES(?,?,?,?,?)",
               (cname, hr_name, email, generate_password_hash(pwd), industry))
            flash("Company registered! Please login.", "success")
            conn.close()
            return redirect(url_for("company_login"))
        conn.close()
    return render_template("company_register.html")


@app.route("/company/login", methods=["GET", "POST"])
def company_login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pwd   = request.form["password"]
        conn  = get_db()
        c     = qd(conn, "SELECT * FROM companies WHERE email=?", (email,), one=True)
        conn.close()
        if c and check_password_hash(c["password"], pwd):
            session.update({"company_id": c["id"], "company_name": c["company_name"],
                            "hr_name": c["hr_name"], "role": "company"})
            return redirect(url_for("hr_dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("company_login.html")


# ══════════════════════════════════════════════════════════════════
# PHASE 2 — RESUME UPLOAD + AI ANALYSIS
# ══════════════════════════════════════════════════════════════════
@app.route("/user/upload", methods=["POST"])
def upload_resume():
    if session.get("role") != "user":
        return redirect(url_for("user_login"))
    f = request.files.get("resume")
    if not f or not allowed(f.filename):
        flash("Please upload a PDF or DOCX file.", "error")
        return redirect(url_for("user_dashboard"))

    fname = secure_filename(f.filename)
    path  = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    f.save(path)

    parsed = parse_resume(path)
    score  = score_resume(parsed)

    conn = get_db()
    rid  = qw(conn,
        "INSERT INTO resumes(user_id,filename,skills,education,experience,score,keywords_json) "
        "VALUES(?,?,?,?,?,?,?)",
        (session["user_id"], fname,
         json.dumps(parsed.get("skills", [])),
         parsed.get("education", ""),
         parsed.get("experience", ""),
         score["overall"],
         json.dumps(score)))
    conn.close()
    return redirect(url_for("resume_result", rid=rid))


@app.route("/user/resume/<int:rid>")
def resume_result(rid):
    if session.get("role") != "user":
        return redirect(url_for("user_login"))
    conn   = get_db()
    resume = qd(conn, "SELECT * FROM resumes WHERE id=? AND user_id=?",
                (rid, session["user_id"]), one=True)
    conn.close()
    if not resume:
        return redirect(url_for("user_dashboard"))

    score       = json.loads(resume["keywords_json"] or "{}")
    skills      = json.loads(resume["skills"] or "[]")
    questions   = generate_interview_questions(skills)
    email_draft = generate_email(session["user_name"], skills)
    return render_template("resume_result.html",
        resume=resume, score=score, skills=skills,
        questions=questions, email_draft=email_draft)


# ══════════════════════════════════════════════════════════════════
# PHASE 3 — JOB PORTAL
# ══════════════════════════════════════════════════════════════════
@app.route("/jobs")
def job_portal():
    conn   = get_db()
    domain = request.args.get("domain", "")
    loc    = request.args.get("location", "")
    skill  = request.args.get("skill", "")

    sql  = ("SELECT j.*, c.company_name as cname "
            "FROM jobs j LEFT JOIN companies c ON j.company_id=c.id WHERE 1=1")
    args = []
    if domain: sql += " AND j.domain=?";                args.append(domain)
    if loc:    sql += " AND j.location LIKE ?";          args.append(f"%{loc}%")
    if skill:  sql += " AND j.skills_required LIKE ?";   args.append(f"%{skill}%")

    jobs    = qd(conn, sql, args)
    domains = qd(conn, "SELECT DISTINCT domain FROM jobs WHERE domain != '' ORDER BY domain")
    conn.close()
    return render_template("job_portal.html", jobs=jobs, domains=domains,
                           filters={"domain": domain, "location": loc, "skill": skill})


@app.route("/jobs/<int:jid>")
def job_detail(jid):
    conn = get_db()
    job  = qd(conn,
        "SELECT j.*, c.company_name as cname "
        "FROM jobs j LEFT JOIN companies c ON j.company_id=c.id WHERE j.id=?",
        (jid,), one=True)
    conn.close()
    if not job:
        return redirect(url_for("job_portal"))

    match_score = None
    if session.get("role") == "user":
        conn   = get_db()
        latest = qd(conn, "SELECT * FROM resumes WHERE user_id=? ORDER BY uploaded_at DESC LIMIT 1",
                    (session["user_id"],), one=True)
        conn.close()
        if latest:
            skills = json.loads(latest["skills"] or "[]")
            match_score = match_resume_to_job(skills, job["skills_required"])
    return render_template("job_detail.html", job=job, match_score=match_score)


@app.route("/jobs/recommend")
def job_recommend():
    if session.get("role") != "user":
        return redirect(url_for("user_login"))
    conn   = get_db()
    latest = qd(conn, "SELECT * FROM resumes WHERE user_id=? ORDER BY uploaded_at DESC LIMIT 1",
                (session["user_id"],), one=True)
    jobs   = qd(conn, "SELECT j.*, c.company_name as cname FROM jobs j LEFT JOIN companies c ON j.company_id=c.id")
    conn.close()
    if not latest:
        flash("Upload your resume first to get AI recommendations!", "error")
        return redirect(url_for("user_dashboard"))
    skills = json.loads(latest["skills"] or "[]")
    ranked = recommend_jobs(skills, jobs)
    return render_template("job_recommend.html", jobs=ranked, name=session["user_name"])


# ══════════════════════════════════════════════════════════════════
# PHASE 4 — HR DASHBOARD + BULK UPLOAD
# ══════════════════════════════════════════════════════════════════
@app.route("/hr/dashboard")
def hr_dashboard():
    if session.get("role") != "company":
        return redirect(url_for("company_login"))
    conn   = get_db()
    cands  = qd(conn,
        "SELECT ca.*, u.name as uname, u.email as uemail "
        "FROM candidates ca JOIN users u ON ca.user_id=u.id "
        "WHERE ca.company_id=? ORDER BY ca.score DESC",
        (session["company_id"],))
    jobs   = qd(conn, "SELECT * FROM jobs WHERE company_id=?", (session["company_id"],))
    stats  = qd(conn,
        "SELECT status, COUNT(*) as cnt FROM candidates WHERE company_id=? GROUP BY status",
        (session["company_id"],))
    conn.close()
    return render_template("hr_dashboard.html",
        company=session["company_name"], hr=session["hr_name"],
        candidates=cands, jobs=jobs, stats=stats)


@app.route("/hr/bulk_upload", methods=["POST"])
def bulk_upload():
    if session.get("role") != "company":
        return redirect(url_for("company_login"))
    files = request.files.getlist("resumes")
    jid   = request.form.get("job_id") or None
    conn  = get_db()
    job   = qd(conn, "SELECT * FROM jobs WHERE id=?", (jid,), one=True) if jid else None
    count = 0

    for f in files:
        if not f or not allowed(f.filename):
            continue
        fname  = secure_filename(f.filename)
        path   = os.path.join(app.config["UPLOAD_FOLDER"], fname)
        f.save(path)

        parsed = parse_resume(path)
        score  = score_resume(parsed)
        match  = match_resume_to_job(parsed.get("skills", []),
                                     job["skills_required"] if job else "") if job else 0

        name  = parsed.get("name", "Unknown")
        email = parsed.get("email") or fname + "@noemail.com"

        uid_row = qd(conn, "SELECT id FROM users WHERE email=?", (email,), one=True)
        if uid_row:
            uid = uid_row["id"]
        else:
            uid = qw(conn,
                "INSERT INTO users(name,email,password,phone) VALUES(?,?,?,'')",
                (name, email, generate_password_hash("changeme123")))

        qw(conn,
            "INSERT INTO candidates(user_id,company_id,job_id,filename,score,match_pct,"
            "skills_json,strengths,weaknesses,hidden_gems,status) VALUES(?,?,?,?,?,?,?,?,?,?,'pending')",
            (uid, session["company_id"], jid, fname, score["overall"], match,
             json.dumps(parsed.get("skills", [])),
             json.dumps(score.get("strengths", [])),
             json.dumps(score.get("weaknesses", [])),
             json.dumps(score.get("hidden_gems", []))))
        count += 1

    conn.close()
    flash(f"{count} resume(s) screened successfully.", "success")
    return redirect(url_for("hr_dashboard"))


@app.route("/hr/candidate/<int:cid>")
def candidate_detail(cid):
    if session.get("role") != "company":
        return redirect(url_for("company_login"))
    conn = get_db()
    c    = qd(conn,
        "SELECT ca.*, u.name as uname, u.email as uemail "
        "FROM candidates ca JOIN users u ON ca.user_id=u.id "
        "WHERE ca.id=? AND ca.company_id=?",
        (cid, session["company_id"]), one=True)
    conn.close()
    if not c:
        return redirect(url_for("hr_dashboard"))
    c["skills"]      = json.loads(c["skills_json"] or "[]")
    c["strengths"]   = json.loads(c["strengths"]   or "[]")
    c["weaknesses"]  = json.loads(c["weaknesses"]  or "[]")
    c["hidden_gems"] = json.loads(c["hidden_gems"] or "[]")
    return render_template("candidate_detail.html", c=c)


@app.route("/hr/candidate/<int:cid>/status", methods=["POST"])
def update_status(cid):
    if session.get("role") != "company":
        return redirect(url_for("company_login"))
    conn = get_db()
    qw(conn, "UPDATE candidates SET status=?, hr_comment=? WHERE id=? AND company_id=?",
       (request.form["status"], request.form.get("comment", ""), cid, session["company_id"]))
    conn.close()
    return redirect(url_for("candidate_detail", cid=cid))


# ══════════════════════════════════════════════════════════════════
# PHASE 5 — RANKINGS
# ══════════════════════════════════════════════════════════════════
@app.route("/hr/ranking")
def ranking():
    if session.get("role") != "company":
        return redirect(url_for("company_login"))
    jid  = request.args.get("job_id", "")
    conn = get_db()
    jobs = qd(conn, "SELECT * FROM jobs WHERE company_id=?", (session["company_id"],))

    sql  = ("SELECT ca.*, u.name as uname "
            "FROM candidates ca JOIN users u ON ca.user_id=u.id "
            "WHERE ca.company_id=?")
    args = [session["company_id"]]
    if jid:
        sql += " AND ca.job_id=?"
        args.append(jid)
    sql += " ORDER BY (ca.score*0.6 + ca.match_pct*0.4) DESC"

    cands = qd(conn, sql, args)
    conn.close()
    for i, c in enumerate(cands):
        c["rank"]        = i + 1
        c["final_score"] = round(float(c["score"]) * 0.6 + float(c["match_pct"]) * 0.4, 1)
    return render_template("ranking.html", candidates=cands, jobs=jobs, selected_job=jid)


# ══════════════════════════════════════════════════════════════════
# POST JOB (HR)
# ══════════════════════════════════════════════════════════════════
@app.route("/hr/post_job", methods=["GET", "POST"])
def post_job():
    if session.get("role") != "company":
        return redirect(url_for("company_login"))
    if request.method == "POST":
        conn = get_db()
        qw(conn,
            "INSERT INTO jobs(company_id,title,location,domain,skills_required,description,salary,job_type) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (session["company_id"], request.form["title"], request.form["location"],
             request.form["domain"], request.form["skills_required"],
             request.form["description"], request.form.get("salary", ""),
             request.form.get("job_type", "Full-time")))
        conn.close()
        flash("Job posted successfully!", "success")
        return redirect(url_for("hr_dashboard"))
    return render_template("post_job.html")


# ──────────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()   # Create tables + seed on first run
    app.run(debug=True)
