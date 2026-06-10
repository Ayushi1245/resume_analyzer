import re
from collections import Counter


STOP_WORDS = {"the", "a", "and", "or", "in", "of", "to", "for", "with", "on", "at",
              "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
              "do", "does", "did", "will", "would", "shall", "should", "may", "might",
              "can", "could", "an", "this", "that", "these", "those", "it", "its",
              "we", "our", "you", "your", "they", "their", "not", "but", "from", "by",
              "as", "if", "all", "each", "every", "both", "any", "such", "no", "nor"}


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text, filtering stopwords."""
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.]*\b', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def keyword_overlap_score(resume_text: str, jd_text: str) -> dict:
    """Deterministic keyword overlap scoring between resume and job description."""
    resume_kw = set(extract_keywords(resume_text))
    jd_kw = Counter(extract_keywords(jd_text))

    # Weight high-frequency JD keywords more — words mentioned 2+ times
    # are likely core requirements, not incidental mentions
    important_jd_kw = {w for w, count in jd_kw.items() if count >= 2}

    matched = resume_kw & important_jd_kw
    missing = important_jd_kw - resume_kw

    score = round(len(matched) / max(len(important_jd_kw), 1) * 100)
    return {
        "keyword_score": score,
        "matched": sorted(matched),
        "missing": sorted(missing),
    }
