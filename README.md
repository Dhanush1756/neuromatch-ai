# 🧠 NeuroMATCH AI
### Intelligent Resume Screening & Internship Matching Platform
**Flask + SQLite + NLP — No MySQL, No Setup Hassle — All 7 Phases**

---

## ⚡ Quick Start (3 steps)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app (database auto-creates on first launch!)
python app.py

# 3. Open browser
#    http://127.0.0.1:5000
```

> ✅ **SQLite is built into Python** — no database installation needed.
> The file `neuromatch.db` is created automatically on first run with all tables + 10 sample jobs.

---

## 📁 Project Structure

```
neuromatch/
├── app.py                      ← Flask app — all routes (Phases 1–7)
├── requirements.txt            ← Only 4 packages needed
├── README.md
├── neuromatch.db               ← Auto-created SQLite database
│
├── nlp/
│   ├── __init__.py
│   ├── resume_parser.py        ← PDF/DOCX text extractor + NER
│   ├── scorer.py               ← AI ensemble scorer (skills+edu+exp)
│   ├── job_matcher.py          ← Semantic resume↔job matching
│   └── ai_features.py          ← Interview Q generator + email writer
│
├── static/
│   └── css/style.css           ← Dark UI theme
│
├── templates/                  ← 14 Jinja2 HTML pages
│   ├── index.html              ← Landing page
│   ├── auth_base.html          ← Auth layout base
│   ├── user_login.html
│   ├── user_register.html
│   ├── company_login.html
│   ├── company_register.html
│   ├── user_dashboard.html     ← Student: upload + history
│   ├── resume_result.html      ← Full AI analysis view
│   ├── job_portal.html         ← Browse + filter jobs
│   ├── job_detail.html         ← Job detail + match score
│   ├── job_recommend.html      ← AI-ranked recommendations
│   ├── hr_dashboard.html       ← HR: bulk upload + candidates
│   ├── candidate_detail.html   ← Individual candidate profile
│   ├── ranking.html            ← 🥇🥈🥉 Podium + full table
│   └── post_job.html           ← HR: post a new job
│
└── uploads/                    ← Uploaded resumes (auto-created)
```

---

## 🔐 Two Login Types

| Role | Register URL | Login URL | Dashboard |
|---|---|---|---|
| 🎓 Student | `/user/register` | `/user/login` | `/user/dashboard` |
| 🏢 HR / Company | `/company/register` | `/company/login` | `/hr/dashboard` |

---

## 🧩 All 7 Phases

| Phase | Feature | Details |
|---|---|---|
| **1** | Auth System | Student + HR register/login with hashed passwords |
| **2** | Resume Analysis | PDF/DOCX upload → NLP parsing → AI scoring |
| **2** | AI Features | Interview Q generator, cover email writer |
| **2** | Score Breakdown | Skills 45% + Education 25% + Experience 30% |
| **2** | Insights | Hidden gems, strengths, weaknesses |
| **3** | Job Portal | Browse, filter by domain/location/skill |
| **3** | Job Detail | View job + your resume match % |
| **3** | AI Recommendations | Jobs ranked by semantic match to your resume |
| **4** | HR Dashboard | View all screened candidates with stats |
| **4** | Bulk Upload | Upload multiple PDF/DOCX resumes at once |
| **4** | Candidate Detail | Full profile: skills, gems, strengths, weaknesses |
| **4** | HR Decision | Shortlist / reject / hire + comments |
| **5** | Auto Ranking | Candidates ranked by Score×0.6 + Match×0.4 |
| **5** | Podium View | Gold 🥇 Silver 🥈 Bronze 🥉 top 3 display |
| **5** | Filter by Job | Rank candidates per job posting |
| **6** | NLP Pipeline | Regex NER + 80+ skill keyword bank |
| **6** | Semantic Match | Jaccard similarity for resume ↔ job matching |
| **6** | Ensemble Scorer | Weighted multi-factor scoring (RF-style) |
| **7** | Full Integration | All routes connected, SQLite auto-init, seeds |

---

## 🤖 AI / NLP Features Detail

### Resume Parser (`nlp/resume_parser.py`)
- Extracts: name, email, phone, skills, education, experience
- Supports: PDF (pdfplumber) + DOCX (python-docx)
- 80+ skill keywords across: languages, frameworks, ML, cloud, databases, tools

### Scorer (`nlp/scorer.py`)
- **Skills Score** (45%): keyword count + premium/emerging skill bonuses
- **Education Score** (25%): degree tier + CGPA bonus
- **Experience Score** (30%): years + action verb analysis
- Identifies: strengths, weaknesses, hidden gems (open source, research, hackathons, etc.)

### Job Matcher (`nlp/job_matcher.py`)
- Jaccard token overlap between resume skills and job requirements
- Returns 0–100% match score
- Powers both job detail view and AI recommendations

### AI Features (`nlp/ai_features.py`)
- 50+ interview questions mapped to 12 skill categories
- Auto-generated cover letter / email using detected skills

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `Flask` | Web framework |
| `Werkzeug` | Password hashing + file utilities |
| `pdfplumber` | PDF text extraction |
| `python-docx` | DOCX text extraction |

> SQLite3 is part of Python's standard library — **no extra install needed**.

---

## 🛠️ Troubleshooting

**`ModuleNotFoundError: pdfplumber`**
```bash
pip install pdfplumber
```

**`ModuleNotFoundError: docx`**
```bash
pip install python-docx
```

**Resume shows 0 skills / score**
→ The PDF may be image-based (scanned). Use a text-based PDF or DOCX.

**Database reset**
→ Delete `neuromatch.db` and restart `python app.py` — it recreates everything.

---

## 🎨 UI Theme
Dark glassmorphism design using:
- **Fonts**: Syne (headings) + DM Sans (body) via Google Fonts
- **Colors**: `#00e5b0` accent green + `#7b5cf0` purple on `#080b14` dark background
- Responsive sidebar layout, animated cards, score rings, progress bars

---

*NeuroMATCH AI · Built with Flask + SQLite + NLP · Phases 1–7 Complete* 🧠
