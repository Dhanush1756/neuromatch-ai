"""Phase 3 + 6 — Semantic job matcher using Jaccard overlap"""
import re

def tokenize(text: str) -> set:
    return set(re.findall(r"[\w\.]+", text.lower()))

def match_resume_to_job(skills: list, job_skills_text: str) -> float:
    if not skills or not job_skills_text:
        return 0.0
    resume_tokens = set(s.lower() for s in skills)
    job_tokens    = tokenize(job_skills_text)
    overlap       = resume_tokens & job_tokens
    pct = len(overlap) / max(len(job_tokens), 1) * 100
    return round(min(pct * 1.25, 100), 1)

def recommend_jobs(skills: list, jobs: list) -> list:
    if not skills:
        return jobs
    scored = []
    for job in jobs:
        pct = match_resume_to_job(skills, job.get("skills_required", ""))
        scored.append({**job, "match_pct": pct})
    return sorted(scored, key=lambda x: x["match_pct"], reverse=True)
