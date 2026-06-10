import streamlit as st
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

from core.parser import extract_text
from core.analyzer import analyze_resume, score_ats, tailor_resume
from core.ats_scorer import keyword_overlap_score
from utils.helpers import count_tokens, truncate_text

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS for premium dark theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25);
    }
    .main-header h1 {
        color: white;
        font-size: 2.4rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: rgba(255, 255, 255, 0.85);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
        font-weight: 300;
    }

    /* Score cards */
    .score-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 16px;
        padding: 1.8rem;
        text-align: center;
        backdrop-filter: blur(10px);
    }
    .score-value {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
    }
    .score-label {
        font-size: 0.9rem;
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.3rem;
    }

    /* Section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(102, 126, 234, 0.3);
    }

    /* Strength/weakness pills */
    .pill-green {
        display: inline-block;
        background: rgba(16, 185, 129, 0.12);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.25);
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .pill-red {
        display: inline-block;
        background: rgba(239, 68, 68, 0.12);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.25);
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .pill-blue {
        display: inline-block;
        background: rgba(59, 130, 246, 0.12);
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.25);
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .pill-orange {
        display: inline-block;
        background: rgba(245, 158, 11, 0.12);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.25);
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.85rem;
        font-weight: 500;
    }

    /* Improvement cards */
    .improvement-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.05));
        border-left: 4px solid #667eea;
        border-radius: 0 12px 12px 0;
        padding: 1.2rem 1.5rem;
        margin: 0.8rem 0;
    }
    .improvement-card strong {
        color: #667eea;
    }

    /* Keyword tags */
    .keyword-matched {
        display: inline-block;
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 0.3rem 0.7rem;
        border-radius: 6px;
        margin: 0.2rem;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .keyword-missing {
        display: inline-block;
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        padding: 0.3rem 0.7rem;
        border-radius: 6px;
        margin: 0.2rem;
        font-size: 0.8rem;
        font-weight: 500;
    }

    /* Privacy badge */
    .privacy-badge {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-size: 0.8rem;
        color: #10b981;
        text-align: center;
    }

    /* Upload area enhancements */
    [data-testid="stFileUploader"] {
        border-radius: 12px;
    }

    /* Hide default Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Smoother transitions */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📄 AI Resume Analyzer & Improver</h1>
    <p>Upload your resume · Get AI-powered insights · Tailor to any job description</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Analysis Settings")
    st.markdown("---")

    mode = st.radio(
        "Analysis Mode",
        ["📊 Analyze Only", "🎯 ATS Score + Tailor"],
        help="Choose 'Analyze Only' for general feedback, or 'ATS Score + Tailor' to optimize for a specific job."
    )

    st.markdown("---")

    st.markdown("### 📖 Score Guide")
    st.markdown("""
    | Score | Rating |
    |-------|--------|
    | 85–100 | ✅ Excellent |
    | 70–84 | 🟡 Good |
    | 50–69 | 🟠 Fair |
    | < 50 | 🔴 Needs Work |
    """)

    st.markdown("---")

    st.markdown("""
    <div class="privacy-badge">
        🔒 Your resume is processed in memory and never stored
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Upload Section
# ─────────────────────────────────────────────
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📎 Upload Your Resume")
    resume_file = st.file_uploader(
        "Drag and drop or click to upload (PDF or DOCX)",
        type=["pdf", "docx"],
        label_visibility="collapsed",
    )
    if resume_file:
        st.success(f"✓ Uploaded: **{resume_file.name}** ({resume_file.size / 1024:.1f} KB)")

with col2:
    jd_text = ""
    if "ATS" in mode:
        st.markdown("### 📋 Job Description")
        jd_text = st.text_area(
            "Paste the job description here",
            height=200,
            placeholder="Paste the full job description to get ATS scoring and a tailored resume...",
            label_visibility="collapsed",
        )
    else:
        st.markdown("### 💡 Tip")
        st.info(
            "Switch to **🎯 ATS Score + Tailor** mode in the sidebar to score your "
            "resume against a specific job posting and get a rewritten version!"
        )

# ─────────────────────────────────────────────
# Analyze Button
# ─────────────────────────────────────────────
st.markdown("")  # spacing

if resume_file:
    analyze_btn = st.button(
        "🚀  Analyze My Resume",
        type="primary",
        use_container_width=True,
    )
else:
    analyze_btn = False
    st.markdown(
        "<p style='text-align:center; opacity:0.5; margin-top:1rem;'>"
        "⬆️ Upload a resume to get started</p>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
# Analysis Pipeline
# ─────────────────────────────────────────────
if resume_file and analyze_btn:
    # Save uploaded file to temp for parsing
    suffix = ".pdf" if resume_file.name.lower().endswith(".pdf") else ".docx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(resume_file.read())
        tmp_path = tmp.name

    try:
        # ── Step 1: Parse ──
        with st.spinner("📖 Parsing resume..."):
            resume_text = extract_text(tmp_path)

        if not resume_text.strip():
            st.error("❌ Could not extract text from the file. It may be image-based (needs OCR).")
            st.stop()

        # Show token count
        token_count = count_tokens(resume_text)
        st.caption(f"📝 Extracted {len(resume_text):,} characters · {token_count:,} tokens")

        # Truncate if needed
        if token_count > 4000:
            resume_text = truncate_text(resume_text, max_tokens=4000)
            st.warning("⚠️ Resume was truncated to 4,000 tokens to stay within AI context limits.")

        st.divider()

        # ── Step 2: General Analysis ──
        with st.spinner("🤖 Analyzing with AI — this may take a moment..."):
            analysis = analyze_resume(resume_text)

        # ── Display: Overall Score ──
        st.markdown('<div class="section-header">📊 Overall Analysis</div>', unsafe_allow_html=True)

        score = analysis.get("overall_score", 0)
        summary = analysis.get("summary", "")

        score_col, summary_col = st.columns([1, 2])

        with score_col:
            # Color based on score
            if score >= 85:
                emoji, label = "🟢", "Excellent"
            elif score >= 70:
                emoji, label = "🟡", "Good"
            elif score >= 50:
                emoji, label = "🟠", "Fair"
            else:
                emoji, label = "🔴", "Needs Work"

            st.markdown(f"""
            <div class="score-card">
                <div class="score-value">{score}</div>
                <div class="score-label">Resume Score</div>
                <div style="margin-top: 0.5rem; font-size: 1.1rem;">{emoji} {label}</div>
            </div>
            """, unsafe_allow_html=True)

        with summary_col:
            st.markdown(f"**AI Summary:** {summary}")
            st.progress(score / 100)

            # Skills identified
            skills = analysis.get("skills_identified", {})
            tech_skills = skills.get("technical", [])
            soft_skills = skills.get("soft", [])

            if tech_skills:
                st.markdown("**Technical Skills Identified:**")
                pills_html = " ".join(f'<span class="pill-blue">{s}</span>' for s in tech_skills[:15])
                st.markdown(pills_html, unsafe_allow_html=True)

            if soft_skills:
                st.markdown("**Soft Skills Identified:**")
                pills_html = " ".join(f'<span class="pill-orange">{s}</span>' for s in soft_skills[:10])
                st.markdown(pills_html, unsafe_allow_html=True)

        # ── Strengths & Weaknesses ──
        st.markdown("")
        str_col, weak_col = st.columns(2)

        with str_col:
            st.markdown("#### ✅ Strengths")
            for s in analysis.get("strengths", []):
                st.markdown(f'<span class="pill-green">✓ {s}</span>', unsafe_allow_html=True)

        with weak_col:
            st.markdown("#### ⚠️ Weaknesses")
            for w in analysis.get("weaknesses", []):
                st.markdown(f'<span class="pill-red">✗ {w}</span>', unsafe_allow_html=True)

        # ── Missing Sections ──
        missing = analysis.get("missing_sections", [])
        if missing:
            st.markdown("#### 📋 Missing Sections")
            pills_html = " ".join(f'<span class="pill-orange">+ {m}</span>' for m in missing)
            st.markdown(pills_html, unsafe_allow_html=True)

        # ── Top 3 Improvements ──
        st.markdown('<div class="section-header">🔝 Top 3 High-Impact Improvements</div>', unsafe_allow_html=True)
        for i, tip in enumerate(analysis.get("top_3_improvements", []), 1):
            st.markdown(f"""
            <div class="improvement-card">
                <strong>#{i}</strong> — {tip}
            </div>
            """, unsafe_allow_html=True)

        # ── Detailed Issues (Expandable) ──
        with st.expander("🛠 Detailed Issues & Suggestions", expanded=False):
            quant_gaps = analysis.get("quantification_gaps", [])
            verb_issues = analysis.get("action_verb_issues", [])
            fmt_issues = analysis.get("formatting_issues", [])

            if quant_gaps:
                st.markdown("**📏 Bullets Missing Metrics:**")
                for g in quant_gaps:
                    st.markdown(f"- _{g}_")

            if verb_issues:
                st.markdown("**💪 Weak Action Verbs:**")
                for v in verb_issues:
                    st.markdown(f"- _{v}_")

            if fmt_issues:
                st.markdown("**🎨 Formatting Issues:**")
                for f in fmt_issues:
                    st.markdown(f"- _{f}_")

            if not (quant_gaps or verb_issues or fmt_issues):
                st.success("No major issues detected — great job! 🎉")

        # ── Step 3: ATS Mode ──
        if "ATS" in mode and jd_text.strip():
            st.divider()
            st.markdown('<div class="section-header">🤖 ATS Compatibility Analysis</div>', unsafe_allow_html=True)

            with st.spinner("🔍 Running ATS analysis..."):
                ats = score_ats(resume_text, jd_text)
                kw_data = keyword_overlap_score(resume_text, jd_text)

            # Blended ATS score (50% LLM + 50% keyword)
            llm_ats = ats.get("ats_score", 0)
            kw_ats = kw_data["keyword_score"]
            ats_score = round((llm_ats + kw_ats) / 2)

            ats_col1, ats_col2, ats_col3 = st.columns(3)

            with ats_col1:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-value">{ats_score}</div>
                    <div class="score-label">Combined ATS Score</div>
                </div>
                """, unsafe_allow_html=True)

            with ats_col2:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-value" style="font-size: 2.5rem;">{llm_ats}</div>
                    <div class="score-label">AI Analysis Score</div>
                </div>
                """, unsafe_allow_html=True)

            with ats_col3:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-value" style="font-size: 2.5rem;">{kw_ats}</div>
                    <div class="score-label">Keyword Match Score</div>
                </div>
                """, unsafe_allow_html=True)

            st.progress(ats_score / 100)

            # Keywords
            kw_col1, kw_col2 = st.columns(2)

            with kw_col1:
                st.markdown("#### ✅ Matched Keywords")
                if kw_data["matched"]:
                    tags = " ".join(f'<span class="keyword-matched">{k}</span>' for k in kw_data["matched"][:25])
                    st.markdown(tags, unsafe_allow_html=True)
                else:
                    st.caption("No keyword matches found")

            with kw_col2:
                st.markdown("#### ❌ Missing Keywords")
                if kw_data["missing"]:
                    tags = " ".join(f'<span class="keyword-missing">{k}</span>' for k in kw_data["missing"][:25])
                    st.markdown(tags, unsafe_allow_html=True)
                else:
                    st.success("All important keywords are covered! 🎉")

            # ATS Recommendations
            recs = ats.get("recommendations", [])
            if recs:
                st.markdown("#### 💡 ATS Recommendations")
                for rec in recs:
                    st.markdown(f"""
                    <div class="improvement-card">
                        {rec}
                    </div>
                    """, unsafe_allow_html=True)

            # Formatting Risks
            risks = ats.get("formatting_ats_risks", [])
            if risks:
                with st.expander("⚠️ ATS Formatting Risks"):
                    for r in risks:
                        st.warning(r)

            # ── Tailored Resume ──
            st.divider()
            st.markdown('<div class="section-header">✍️ Tailored Resume</div>', unsafe_allow_html=True)
            st.caption("Your resume rewritten to match the job description — no fabricated experience")

            with st.spinner("✍️ Rewriting resume for this job — please wait..."):
                tailored = tailor_resume(resume_text, jd_text)

            st.text_area(
                "Tailored Resume (select all → copy):",
                tailored,
                height=400,
                label_visibility="visible",
            )

            st.download_button(
                "⬇️  Download Tailored Resume (.txt)",
                data=tailored,
                file_name="tailored_resume.txt",
                mime="text/plain",
                use_container_width=True,
            )

        elif "ATS" in mode and not jd_text.strip():
            st.divider()
            st.warning("📋 Paste a job description in the right panel to get ATS scoring and a tailored resume.")

    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.caption("Please check your API key in .env and try again.")

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
