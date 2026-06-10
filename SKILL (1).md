---
name: ai-resume-analyzer
description: >
  Build, run, or improve an AI-powered Resume Analyzer & Improver application.
  Use this skill whenever the user mentions: resume analysis, CV review, ATS scoring,
  job description tailoring, resume improvement suggestions, skill gap analysis,
  resume parser, or any project that involves uploading a resume and getting AI feedback.
  Also trigger when the user asks how to build a resume tool with Streamlit, LangChain,
  OpenAI, Gemini, or Hugging Face. Even if the user only says "analyze my resume" or
  "make my resume better for this job", use this skill — it directly applies.
  Covers: project scaffolding, LLM integration, ATS scoring logic, PDF/DOCX parsing,
  Streamlit UI design, prompt engineering for resume critique, and deployment.
---

# AI Resume Analyzer & Improver

A skill for building (or running) a full-stack AI application that:
1. **Parses** an uploaded resume (PDF or DOCX)
2. **Analyzes** skills, experience, and formatting
3. **Scores** ATS (Applicant Tracking System) compatibility
4. **Tailors** the resume to a given job description
5. **Outputs** specific, actionable improvement suggestions

---

## Tech Stack

| Layer | Recommended | Alternatives |
|---|---|---|
| LLM | `claude-sonnet-4-20250514` via Anthropic API | OpenAI GPT-4o, Google Gemini 1.5 Pro |
| Orchestration | LangChain (`langchain`, `langchain-anthropic`) | Direct API calls (simpler for small apps) |
| UI | Streamlit | Gradio, FastAPI + React |
| PDF Parsing | `pdfplumber` or `PyMuPDF` | `pdfminer.six` |
| DOCX Parsing | `python-docx` | `docx2txt` |
| ATS Scoring | Custom keyword-matching + LLM judgment | spaCy NER + TF-IDF |
| Deployment | Streamlit Community Cloud | Hugging Face Spaces, Railway, Render |

---

## Project Structure

```
resume-analyzer/
├── app.py                  # Streamlit entry point
├── core/
│   ├── parser.py           # PDF/DOCX text extraction
│   ├── analyzer.py         # LLM analysis chains
│   ├── ats_scorer.py       # ATS compatibility scoring
│   └── tailoring.py        # Job-description-specific rewrite
├── prompts/
│   ├── analyze.txt         # System prompt for resume analysis
│   ├── ats_score.txt       # Prompt for ATS scoring
│   └── tailor.txt          # Prompt for JD-specific tailoring
├── utils/
│   └── helpers.py          # Chunking, formatting, token counting
├── requirements.txt
└── .env.example
```

---

## Step-by-Step Build Guide

### Step 1 — Environment Setup

```bash
python -m venv venv && source venv/bin/activate
pip install streamlit langchain langchain-anthropic \
            pdfplumber python-docx python-dotenv \
            tiktoken
```

Create `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

---

### Step 2 — Resume Parser (`core/parser.py`)

```python
import pdfplumber
from docx import Document
from pathlib import Path

def extract_text(file_path: str) -> str:
    """Extract plain text from PDF or DOCX."""
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        return _parse_pdf(file_path)
    elif path.suffix.lower() in (".docx", ".doc"):
        return _parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

def _parse_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)

def _parse_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
```

**Key tip:** Always strip whitespace aggressively — resume PDFs often have stray newlines and spaces that inflate token counts.

---

### Step 3 — Prompt Engineering (`prompts/`)

#### `prompts/analyze.txt` — General Resume Analysis

```
You are an expert career coach and resume strategist with 15+ years of experience
hiring across tech, finance, and consulting.

Analyze the following resume and return a structured JSON response with these exact keys:

{
  "overall_score": <int 0-100>,
  "summary": "<2-sentence overall impression>",
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
  "missing_sections": ["<e.g., 'Projects', 'Certifications'>"],
  "skills_identified": {
    "technical": ["<skill>", ...],
    "soft": ["<skill>", ...]
  },
  "quantification_gaps": ["<bullet that lacks metrics, e.g., 'Improved system performance'>"],
  "action_verb_issues": ["<weak verb usage, e.g., 'Was responsible for...'"],
  "formatting_issues": ["<e.g., 'Inconsistent date formats'>"],
  "top_3_improvements": ["<highest-impact fix 1>", "<fix 2>", "<fix 3>"]
}

Return ONLY valid JSON. No preamble or markdown fences.

RESUME:
{resume_text}
```

#### `prompts/ats_score.txt` — ATS Compatibility Scoring

```
You are an ATS (Applicant Tracking System) simulation engine.

Score the following resume against the job description below.
Return a JSON object with these keys:

{
  "ats_score": <int 0-100>,
  "keyword_matches": ["<matched keyword>", ...],
  "missing_keywords": ["<important keyword not found>", ...],
  "keyword_density_issues": "<string, e.g., 'Python mentioned 0 times but required'>",
  "formatting_ats_risks": ["<e.g., 'Tables may not parse correctly'>", ...],
  "recommendations": ["<specific fix>", ...]
}

ATS scoring criteria:
- Keyword match rate (40%): Does the resume contain the exact words from the JD?
- Section structure (20%): Are standard sections present (Experience, Education, Skills)?
- Formatting safety (20%): No tables, no text boxes, no headers/footers with key info?
- Quantified impact (20%): Are achievements backed by numbers?

Return ONLY valid JSON.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}
```

#### `prompts/tailor.txt` — JD-Specific Resume Rewrite

```
You are a professional resume writer. Rewrite the resume below to be optimized for
the given job description WITHOUT fabricating any experience or credentials.

Rules:
1. Mirror keywords from the JD naturally in the resume
2. Reorder bullet points so the most relevant ones come first
3. Strengthen weak action verbs (e.g., "helped" → "collaborated to deliver")
4. Add quantification placeholders like "[X%]" where metrics are missing
5. Keep the same overall structure, just optimize wording

Return ONLY the full improved resume text. No commentary.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}
```

---

### Step 4 — LLM Analyzer (`core/analyzer.py`)

```python
import json
import os
from langchain_anthropic import ChatAnthropic
from langchain.prompts import PromptTemplate
from pathlib import Path

llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0.2,
    max_tokens=2048,
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

def _load_prompt(filename: str) -> str:
    return (Path(__file__).parent.parent / "prompts" / filename).read_text()

def analyze_resume(resume_text: str) -> dict:
    prompt = PromptTemplate.from_template(_load_prompt("analyze.txt"))
    chain = prompt | llm
    response = chain.invoke({"resume_text": resume_text})
    return json.loads(response.content)

def score_ats(resume_text: str, job_description: str) -> dict:
    prompt = PromptTemplate.from_template(_load_prompt("ats_score.txt"))
    chain = prompt | llm
    response = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description
    })
    return json.loads(response.content)

def tailor_resume(resume_text: str, job_description: str) -> str:
    prompt = PromptTemplate.from_template(_load_prompt("tailor.txt"))
    chain = prompt | llm
    response = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description
    })
    return response.content
```

**Important:** Use `temperature=0.2` for scoring/analysis (consistency) and `temperature=0.5` for rewriting (creativity).

---

### Step 5 — ATS Scorer (`core/ats_scorer.py`)

Supplement the LLM score with a fast deterministic keyword check:

```python
import re
from collections import Counter

STOP_WORDS = {"the", "a", "and", "or", "in", "of", "to", "for", "with", "on", "at"}

def extract_keywords(text: str) -> list[str]:
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#.]*\b', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]

def keyword_overlap_score(resume_text: str, jd_text: str) -> dict:
    resume_kw = set(extract_keywords(resume_text))
    jd_kw = Counter(extract_keywords(jd_text))
    
    # Weight high-frequency JD keywords more
    important_jd_kw = {w for w, count in jd_kw.items() if count >= 2}
    
    matched = resume_kw & important_jd_kw
    missing = important_jd_kw - resume_kw
    
    score = round(len(matched) / max(len(important_jd_kw), 1) * 100)
    return {
        "keyword_score": score,
        "matched": sorted(matched),
        "missing": sorted(missing),
    }
```

Combine this score with the LLM's ATS score (e.g., 50/50 blend) for a more reliable final number.

---

### Step 6 — Streamlit UI (`app.py`)

```python
import streamlit as st
import tempfile, os
from core.parser import extract_text
from core.analyzer import analyze_resume, score_ats, tailor_resume
from core.ats_scorer import keyword_overlap_score

st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
st.title("📄 AI Resume Analyzer & Improver")
st.caption("Upload your resume · Get ATS score · Tailor to any job")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")
    mode = st.radio("Mode", ["Analyze Only", "ATS Score + Tailor"])
    st.divider()
    st.info("Your resume is processed in memory and never stored.")

# --- Upload ---
col1, col2 = st.columns([1, 1])
with col1:
    resume_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
with col2:
    jd_text = ""
    if mode == "ATS Score + Tailor":
        jd_text = st.text_area("Paste Job Description", height=200)

if resume_file and st.button("🚀 Analyze Resume", type="primary"):
    # Save to temp file for parsing
    suffix = ".pdf" if resume_file.name.endswith(".pdf") else ".docx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(resume_file.read())
        tmp_path = tmp.name

    try:
        with st.spinner("Parsing resume..."):
            resume_text = extract_text(tmp_path)

        # --- General Analysis ---
        with st.spinner("Analyzing with AI..."):
            analysis = analyze_resume(resume_text)

        st.divider()
        st.subheader("📊 Overall Analysis")

        # Score gauge
        score = analysis.get("overall_score", 0)
        color = "green" if score >= 75 else "orange" if score >= 50 else "red"
        st.metric("Overall Resume Score", f"{score}/100")
        st.progress(score / 100)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### ✅ Strengths")
            for s in analysis.get("strengths", []):
                st.markdown(f"- {s}")
        with c2:
            st.markdown("### ⚠️ Weaknesses")
            for w in analysis.get("weaknesses", []):
                st.markdown(f"- {w}")

        st.markdown("### 🔝 Top 3 High-Impact Improvements")
        for i, tip in enumerate(analysis.get("top_3_improvements", []), 1):
            st.info(f"**{i}.** {tip}")

        with st.expander("🛠 Detailed Issues"):
            if analysis.get("quantification_gaps"):
                st.markdown("**Bullets missing metrics:**")
                for g in analysis["quantification_gaps"]:
                    st.markdown(f"- _{g}_")
            if analysis.get("action_verb_issues"):
                st.markdown("**Weak action verbs:**")
                for v in analysis["action_verb_issues"]:
                    st.markdown(f"- _{v}_")

        # --- ATS Mode ---
        if mode == "ATS Score + Tailor" and jd_text.strip():
            st.divider()
            st.subheader("🤖 ATS Compatibility")

            with st.spinner("Running ATS analysis..."):
                ats = score_ats(resume_text, jd_text)
                kw_data = keyword_overlap_score(resume_text, jd_text)

            ats_score = round((ats.get("ats_score", 0) + kw_data["keyword_score"]) / 2)
            st.metric("ATS Compatibility Score", f"{ats_score}/100")
            st.progress(ats_score / 100)

            col3, col4 = st.columns(2)
            with col3:
                st.markdown("**✅ Matched Keywords**")
                st.write(", ".join(kw_data["matched"][:20]) or "None found")
            with col4:
                st.markdown("**❌ Missing Keywords**")
                st.write(", ".join(kw_data["missing"][:20]) or "All covered!")

            st.divider()
            st.subheader("✍️ Tailored Resume")
            with st.spinner("Rewriting resume for this job..."):
                tailored = tailor_resume(resume_text, jd_text)
            st.text_area("Tailored Resume (copy & paste):", tailored, height=400)
            st.download_button("⬇️ Download Tailored Resume (.txt)",
                               data=tailored,
                               file_name="tailored_resume.txt",
                               mime="text/plain")

    finally:
        os.unlink(tmp_path)
```

---

## ATS Score Interpretation

| Score | Meaning | Action |
|---|---|---|
| 85–100 | ✅ Excellent | Apply now |
| 70–84 | 🟡 Good | Minor keyword tweaks |
| 50–69 | 🟠 Fair | Use tailor mode, add missing keywords |
| < 50 | 🔴 Poor | Significant rewrite needed |

---

## Prompt Engineering Tips

- **Be explicit about JSON-only output.** Add `"Return ONLY valid JSON. No preamble."` to every structured prompt. Parse defensively with `try/except`.
- **Chunk long resumes.** If `len(resume_text) > 6000` characters, summarize per-section before the full analysis to stay within context windows.
- **Few-shot examples** dramatically improve quality for ATS scoring. Add 1–2 example resume snippets + expected JSON in the prompt for calibration.
- **Temperature matters.** Use `0.1–0.2` for scoring (you want determinism), `0.4–0.6` for rewrites (you want natural language variety).

---

## Common Pitfalls & Fixes

| Problem | Fix |
|---|---|
| PDF text comes out garbled | Try `PyMuPDF` (`fitz`) as fallback; check if the PDF is image-based (needs OCR) |
| LLM returns markdown-wrapped JSON | Strip ` ```json ` fences before `json.loads()` |
| ATS score varies wildly per run | Lower temperature; add "be consistent" to system prompt |
| Tailored resume fabricates experience | Add explicit rule: "NEVER invent credentials" |
| Slow response in Streamlit | Use `st.cache_data` on the parser; stream LLM output with `stream=True` |
| Token limit exceeded for long resumes | Truncate to 4000 tokens; use `tiktoken` to count before sending |

---

## Deployment (Streamlit Community Cloud)

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → Select repo
3. Add `ANTHROPIC_API_KEY` in **Secrets** (Settings → Secrets)
4. Set main file path to `app.py`

For **Hugging Face Spaces**:
- Use SDK: `streamlit`
- Add secret key via Space Settings → Repository Secrets

---

## Extensions & Ideas

- **LinkedIn Import**: Scrape LinkedIn profile as resume source using Playwright
- **Side-by-side diff view**: Show original vs. tailored resume with highlighted changes
- **Multi-JD comparison**: Score one resume against 5 job descriptions at once
- **Resume version history**: Store past analyses in SQLite or Supabase
- **Cover letter generator**: Feed tailored resume + JD → auto-generate cover letter
- **Interview Q generator**: Based on resume gaps, predict likely interview questions

---

## References

- Read `references/prompt_templates.md` for extended few-shot prompt examples
- Read `references/ats_keyword_lists.md` for curated keyword banks by industry
