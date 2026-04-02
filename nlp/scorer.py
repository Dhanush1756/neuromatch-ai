"""
Phase 2 + 6 — Resume Scorer
Weighted ensemble: Skills 45% + Education 25% + Experience 30%
Also produces: strengths, weaknesses, hidden gems
"""

PREMIUM_SKILLS = {
    "machine learning","deep learning","bert","pytorch","tensorflow","nlp",
    "kubernetes","aws","gcp","azure","docker","react","node.js","fastapi",
    "postgresql","mongodb","spark","hadoop","blockchain","cybersecurity",
    "langchain","computer vision",
}

EMERGING_SKILLS = {
    "rust","kotlin","flutter","graphql","next.js","langchain","llm",
    "mlops","rag","stable diffusion","typescript","fastapi","go",
}

DEGREE_SCORES = {
    "phd":100,"m.tech":90,"msc":85,"m.sc":85,"mba":80,"mca":80,
    "b.tech":75,"b.e":75,"bsc":65,"b.sc":65,"bca":60,"diploma":50,
}


def _extract_cgpa(text: str) -> float:
    import re
    m = re.search(r"(\d+\.?\d*)\s*(cgpa|gpa|/10|/4)", text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        if val <= 4:
            val *= 25   # convert /4 → /100
        return val
    return 0


def score_education(edu_text: str) -> float:
    low = edu_text.lower()
    for deg, sc in DEGREE_SCORES.items():
        if deg in low:
            cgpa  = _extract_cgpa(low)
            bonus = (cgpa - 6) * 2 if cgpa > 0 else 0
            return min(sc + bonus, 100)
    return 40


def score_skills(skills: list) -> dict:
    if not skills:
        return {"score": 0, "premium": [], "emerging": [], "common": []}
    premium  = [s for s in skills if s in PREMIUM_SKILLS]
    emerging = [s for s in skills if s in EMERGING_SKILLS]
    common   = [s for s in skills if s not in PREMIUM_SKILLS and s not in EMERGING_SKILLS]
    base     = min(len(skills) * 4, 55)
    bonus    = min(len(premium) * 5 + len(emerging) * 7, 45)
    return {
        "score":    min(base + bonus, 100),
        "premium":  premium,
        "emerging": emerging,
        "common":   common,
    }


def score_experience(exp_text: str, years: float) -> float:
    base  = min(years * 12, 60)
    kws   = ["led","built","developed","deployed","designed","improved","reduced",
             "increased","achieved","managed","implemented","launched","created"]
    hits  = sum(1 for k in kws if k in exp_text.lower())
    bonus = min(hits * 4, 40)
    return min(base + bonus, 100)


def identify_strengths(parsed: dict, sd: dict) -> list:
    out = []
    if len(parsed["skills"]) > 8:
        out.append(f"Broad skill set ({len(parsed['skills'])} skills detected)")
    if sd["premium"]:
        out.append(f"High-demand skills: {', '.join(sd['premium'][:3])}")
    if parsed["years_exp"] >= 1:
        out.append(f"{int(parsed['years_exp'])}+ years of experience")
    edu = parsed.get("education", "").lower()
    if any(x in edu for x in ["iit", "nit", "bits"]):
        out.append("Prestigious institution (IIT/NIT/BITS)")
    return out or ["Entry-level profile — strong growth potential"]


def identify_weaknesses(parsed: dict) -> list:
    out = []
    if len(parsed["skills"]) < 5:
        out.append("Limited skills listed — add more to your resume")
    if parsed["years_exp"] < 1:
        out.append("No significant work experience yet")
    if not parsed["education"]:
        out.append("Education section unclear or missing")
    missing = {"python", "sql", "git"} - set(parsed["skills"])
    if missing:
        out.append(f"Missing core skills: {', '.join(missing)}")
    return out or ["No major weaknesses detected"]


def identify_hidden_gems(parsed: dict, sd: dict) -> list:
    gems = []
    if sd["emerging"]:
        gems.append(f"🔮 Emerging tech expertise: {', '.join(sd['emerging'])}")
    text = (parsed.get("raw_text", "") + parsed.get("experience", "")).lower()
    if "open source" in text or "github" in text:
        gems.append("🌟 Open source / GitHub contributions")
    if "research" in text or "publication" in text or "paper" in text:
        gems.append("📄 Research / publication background")
    if "hackathon" in text or "competition" in text:
        gems.append("🏆 Hackathon / competition experience")
    if "freelance" in text:
        gems.append("💼 Freelance project experience")
    if "startup" in text or "founded" in text:
        gems.append("🚀 Entrepreneurial / startup exposure")
    return gems or ["No additional hidden gems detected"]


def score_resume(parsed: dict) -> dict:
    sd      = score_skills(parsed.get("skills", []))
    edu_sc  = score_education(parsed.get("education", ""))
    exp_sc  = score_experience(parsed.get("experience", ""), parsed.get("years_exp", 0))
    overall = round(sd["score"] * 0.45 + edu_sc * 0.25 + exp_sc * 0.30, 1)

    from nlp.resume_parser import SKILL_KEYWORDS
    kw_pct = round(len(parsed.get("skills", [])) / max(len(SKILL_KEYWORDS), 1) * 100, 1)

    return {
        "overall":        overall,
        "skills_score":   sd["score"],
        "edu_score":      edu_sc,
        "exp_score":      exp_sc,
        "keyword_pct":    kw_pct,
        "strengths":      identify_strengths(parsed, sd),
        "weaknesses":     identify_weaknesses(parsed),
        "hidden_gems":    identify_hidden_gems(parsed, sd),
        "premium_skills": sd["premium"],
        "emerging_skills":sd["emerging"],
    }
