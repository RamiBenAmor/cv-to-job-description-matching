from sentence_transformers import SentenceTransformer, util
def compute_sbert_similarity(cv_text, jd_text):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    resume_embeddings = model.encode(cv_text, convert_to_tensor=True)
    jd_embedding = model.encode(jd_text, convert_to_tensor=True)

    similarity_scores = util.pytorch_cos_sim(resume_embeddings, jd_embedding)
    return similarity_scores.flatten().tolist()[0]

import re
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer, util
import math

model = SentenceTransformer("all-MiniLM-L6-v2")

TITLE_GROUPS = {
    "Information Technology": ['information-technology', 'it', 'software engineer', 'python developer', 'backend engineer'],
    "Business Development": ['business-development', 'biz dev', 'growth manager', 'business strategist'],
    "Legal": ['advocate', 'lawyer', 'legal advisor'],
    "Culinary": ['chef', 'cook', 'head chef'],
    "Engineering": ['engineering', 'mechanical engineer', 'civil engineer', 'electrical engineer'],
    "Accounting & Finance": ['accountant', 'finance', 'financial analyst', 'auditor'],
    "Fitness & Health": ['fitness', 'healthcare', 'personal trainer', 'physiotherapist'],
    "Aviation": ['aviation', 'pilot', 'air traffic controller'],
    "Sales": ['sales', 'salesperson', 'sales executive'],
    "Banking": ['banking', 'bank officer', 'loan officer'],
    "Consulting": ['consultant', 'strategy consultant', 'business consultant'],
    "Construction": ['construction', 'builder', 'site engineer'],
    "Public Relations": ['public-relations', 'pr manager', 'communications officer'],
    "Human Resources": ['hr', 'recruiter', 'talent acquisition'],
    "Design": ['designer', 'graphic designer', 'ux', 'ui'],
    "Arts & Media": ['arts', 'digital-media', 'media specialist', 'visual artist'],
    "Education": ['teacher', 'educator', 'professor', 'trainer'],
    "Apparel": ['apparel', 'fashion designer', 'clothing'],
    "Agriculture": ['agriculture', 'farmer', 'agronomist'],
    "Automobile": ['automobile', 'car technician', 'auto engineer'],
    "BPO": ['bpo', 'call center agent', 'customer support'],
}

def normalize_title(raw_title: str) -> str:
    raw_title = raw_title.lower().strip()
    for group, aliases in TITLE_GROUPS.items():
        for alias in aliases:
            if SequenceMatcher(None, raw_title, alias).ratio() >= 0.75:
                return group
    return raw_title.title()

def title_similarity(cv_text: str, jd_text: str) -> float:
    cv_title = cv_text.strip().split('\n')[0]
    jd_title = jd_text.strip().split('\n')[0]
    norm_cv = normalize_title(cv_title)
    norm_jd = normalize_title(jd_title)
    emb_cv = model.encode(norm_cv, convert_to_tensor=True)
    emb_jd = model.encode(norm_jd, convert_to_tensor=True)
    return float(util.pytorch_cos_sim(emb_cv, emb_jd)[0][0])

def extract_section(text: str, name: str) -> str:
    pattern = fr"{name}\s*[:\-]?\s*(.*?)(?=\n[A-Z][a-z]|$)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_experience_sentences(section: str) -> str:
    keywords = ("experience", "worked", "developed", "led",
                "managed", "built", "deployed", "implemented")
    sentences = re.split(r"[.\n]", section)
    return " ".join(
        s.strip() for s in sentences if any(k in s.lower() for k in keywords)
    )

def extract_years(section: str) -> int:
    years = re.findall(r"(\d+)\s*(?:\+)?\s*(?:years?|yrs?)", section.lower())
    return max([int(y) for y in years], default=0)

def sbert_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    emb_a = model.encode(a, convert_to_tensor=True)
    emb_b = model.encode(b, convert_to_tensor=True)
    return float(util.pytorch_cos_sim(emb_a, emb_b)[0][0])

def compute_sbert_similarity(cv_text: str, jd_text: str) -> float:
    return sbert_similarity(cv_text, jd_text)

def penalize_exp_gap(score: float, exp_gap: int) -> float:
    # Penalization factor (exponential decay)
    penalty = math.exp(-0.2 * exp_gap)
    return score * penalty

def match_cv_to_jd(cv_text: str, jd_text: str) -> dict:
    # Weights according to your request
    weights = {
        "full_text": 0.4,
        "skills": 0.15,
        "experience": 0.15,
        "title": 0.3
    }

    cv_skills = extract_section(cv_text, "Skills")
    jd_skills = extract_section(jd_text, "Skills")
    skill_sim = sbert_similarity(cv_skills, jd_skills)

    cv_exp = extract_section(cv_text, "Experience")
    jd_exp = extract_section(jd_text, "Experience")
    cv_exp_sent = extract_experience_sentences(cv_exp)
    jd_exp_sent = extract_experience_sentences(jd_exp)
    exp_sim = sbert_similarity(cv_exp_sent, jd_exp_sent)

    cv_years = extract_years(cv_exp)
    jd_years = extract_years(jd_exp)
    exp_gap = max(jd_years - cv_years, 0)

    title_sim = title_similarity(cv_text, jd_text)

    full_text_sim = compute_sbert_similarity(cv_text, jd_text)

    raw_score = (
        weights["full_text"] * full_text_sim +
        weights["skills"] * skill_sim +
        weights["experience"] * exp_sim +
        weights["title"] * title_sim
    )

    final_score = penalize_exp_gap(raw_score, exp_gap)

    return {
        "MatchingScoreRaw": round(raw_score, 3),
        "MatchingScorePenalized": round(final_score, 3),
        "FullTextSimilarity": round(full_text_sim, 3),
        "SkillSimilarity": round(skill_sim, 3),
        "ExperienceSimilarity": round(exp_sim, 3),
        "TitleSimilarity": round(title_sim, 3),
        "CV_Years": cv_years,
        "JD_Years": jd_years,
        "ExperienceGap": exp_gap
    }
#TEST
cv = """
    Senior Accountant
    Skills: Financial reporting, SAP, Excel, Tax Compliance
    Experience: Over 3 years of experience managing accounts, preparing audits and budgets. Worked with SAP for tax reporting.
    """

jd = """
    Accountant
    Skills: Accounting, Tax Reporting, Financial Audits
    Experience: Candidate must have 5+ years experience in financial statements, budget preparation and using SAP.
    """

print(match_cv_to_jd(cv, jd))