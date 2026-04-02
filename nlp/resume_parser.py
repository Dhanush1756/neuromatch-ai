"""
Phase 2 + 6 — Resume Parser
Extracts: name, email, phone, skills, education, experience
Supports: PDF (pdfplumber) + DOCX (python-docx)
"""

import re
import os

# ── Optional imports ──────────────────────────────────────────────
try:
    import pdfplumber
    PDF_OK = True
except ImportError:
    PDF_OK = False

try:
    from docx import Document
    DOCX_OK = True
except ImportError:
    DOCX_OK = False

# ── Skill keyword bank ────────────────────────────────────────────
SKILL_KEYWORDS = {
    # Languages
    "python","java","javascript","typescript","c++","c#","go","rust",
    "kotlin","swift","r","scala","perl","ruby","php","matlab","bash","shell",
    # Web
    "html","css","react","angular","vue","node.js","django","flask","fastapi",
    "spring","express","next.js","nuxt","tailwind","bootstrap","jquery",
    "graphql","rest api","restful",
    # Data / ML / AI
    "machine learning","deep learning","nlp","natural language processing",
    "computer vision","tensorflow","pytorch","keras","scikit-learn","xgboost",
    "lightgbm","bert","gpt","pandas","numpy","matplotlib","seaborn","plotly",
    "spark","hadoop","data analysis","statistics",
    # Databases
    "sql","mysql","postgresql","mongodb","redis","firebase","elasticsearch",
    "sqlite","oracle","cassandra","dynamodb",
    # Cloud / DevOps
    "aws","azure","gcp","docker","kubernetes","terraform","ansible","jenkins",
    "github actions","ci/cd","linux","unix","nginx","apache",
    # Tools
    "git","github","jira","figma","adobe xd","postman","tableau","power bi",
    "excel","word","powerpoint","notion",
    # Soft skills
    "leadership","communication","teamwork","problem solving","critical thinking",
    "time management","project management","agile","scrum",
    # Other
    "android","ios","flutter","react native","unity","blockchain",
    "cybersecurity","networking","opencv","selenium","scrapy","langchain",
}

EDU_HEADERS    = ["education","qualification","academic","degree","school","college","university"]
EXP_HEADERS    = ["experience","employment","work history","internship","project","career"]


def extract_text(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        if not PDF_OK:
            return "[pdfplumber not installed – run: pip install pdfplumber]"
        text = ""
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
        except Exception as e:
            text = f"[PDF read error: {e}]"
        return text
    elif ext == "docx":
        if not DOCX_OK:
            return "[python-docx not installed – run: pip install python-docx]"
        try:
            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"[DOCX read error: {e}]"
    return ""


def extract_email(text: str) -> str:
    m = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else ""


def extract_phone(text: str) -> str:
    m = re.search(r"(\+91[\-\s]?)?[6-9]\d{9}", text)
    return m.group(0) if m else ""


def extract_name(text: str) -> str:
    for line in text.strip().splitlines()[:8]:
        line = line.strip()
        if 3 < len(line) < 55 and "@" not in line and "|" not in line:
            words = line.split()
            if 1 <= len(words) <= 5:
                if all(w[0].isupper() for w in words if w and w[0].isalpha()):
                    return line
    return "Candidate"


def extract_skills(text: str) -> list:
    lower = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, lower):
            found.append(skill)
    return sorted(set(found))


def extract_section(text: str, headers: list, max_lines: int = 15) -> str:
    lines   = text.splitlines()
    result  = []
    capture = False
    for line in lines:
        low = line.lower().strip()
        if any(h in low for h in headers):
            capture = True
        if capture:
            result.append(line)
            if len(result) >= max_lines:
                break
    return "\n".join(result)


def calculate_years_exp(text: str) -> float:
    years = re.findall(r"\b(20\d{2})\b", text)
    if len(years) >= 2:
        ys = sorted(set(int(y) for y in years))
        return min(ys[-1] - ys[0], 20)
    return 0


def parse_resume(path: str) -> dict:
    text = extract_text(path)
    if not text.strip():
        return {"name": "Unknown", "email": "", "phone": "", "skills": [],
                "education": "", "experience": "", "raw_text": "", "years_exp": 0}
    return {
        "name":       extract_name(text),
        "email":      extract_email(text),
        "phone":      extract_phone(text),
        "skills":     extract_skills(text),
        "education":  extract_section(text, EDU_HEADERS),
        "experience": extract_section(text, EXP_HEADERS),
        "raw_text":   text,
        "years_exp":  calculate_years_exp(text),
    }
