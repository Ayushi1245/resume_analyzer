import streamlit as st
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

from core.parser import extract_text, scan_stray_artifacts
from core.analyzer import analyze_resume, score_ats, tailor_resume

st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Simple Resume Analyzer")
st.markdown("Upload your resume and optionally paste a job description to get optimization insights and ATS scoring.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF or Word Document", type=["pdf", "docx", "doc"])

with col2:
    st.subheader("2. Target Job Description (Optional)")
    job_description = st.text_area("Paste the job description here for ATS targeting...", height=150)

if st.button("Analyze Resume", type="primary"):
    if not uploaded_file:
        st.error("Please upload a resume to begin.")
    else:
        with st.spinner("Analyzing resume..."):
            # Save uploaded file to a temporary file
            suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            try:
                # Extract text (raw for artifact scanning, cleaned for LLM)
                resume_text = extract_text(tmp_path)
                
                # Deterministic artifact scan on the extracted text
                artifact_findings = scan_stray_artifacts(resume_text)
                
                st.markdown("---")
                
                # Analyze resume
                st.header("📊 Resume Analysis")
                analysis_results = analyze_resume(resume_text)
                
                # --- Score Metrics Row ---
                score_col1, score_col2 = st.columns(2)
                with score_col1:
                    overall = analysis_results.get("overall_score", 0)
                    st.metric(label="📋 Overall Resume Score", value=f"{overall}/100")
                with score_col2:
                    ats_ready = analysis_results.get("ats_readiness_score", 0)
                    st.metric(label="🤖 ATS Readiness Score", value=f"{ats_ready}/100")
                
                st.subheader("Executive Summary")
                st.write(analysis_results.get("summary", "No summary available."))
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("✅ Strengths")
                    for s in analysis_results.get("strengths", []):
                        st.markdown(f"- {s}")
                with col_b:
                    st.subheader("💡 Top Improvements")
                    for item in analysis_results.get("top_3_improvements", []):
                        st.markdown(f"- {item}")
                
                skills = analysis_results.get("skills_identified", {})
                if skills.get("technical") or skills.get("soft"):
                    st.subheader("🛠️ Identified Skills")
                    if skills.get("technical"):
                        st.markdown("**Technical:** " + ", ".join(skills.get("technical", [])))
                    if skills.get("soft"):
                        st.markdown("**Soft:** " + ", ".join(skills.get("soft", [])))
                
                # --- Grammar & Language Issues ---
                grammar_issues = analysis_results.get("grammar_and_language", [])
                if grammar_issues:
                    st.markdown("---")
                    st.header("✏️ Grammar & Language Corrections")
                    st.caption("These are specific issues found in your resume text. Fix them to sound more professional.")
                    for i, issue in enumerate(grammar_issues, 1):
                        with st.expander(f"Issue {i}: {issue.get('issue', 'Grammar issue')}", expanded=True):
                            st.markdown(f"**❌ Original:** `{issue.get('original', '')}`")
                            st.markdown(f"**✅ Corrected:** `{issue.get('corrected', '')}`")
                            st.markdown(f"**Why:** {issue.get('issue', '')}")
                
                # --- Action Verb Issues ---
                verb_issues = analysis_results.get("action_verb_issues", [])
                if verb_issues:
                    st.markdown("---")
                    st.header("💪 Weak Phrasing — Before & After")
                    st.caption("Replace passive or weak language with strong, impactful action verbs.")
                    for item in verb_issues:
                        if isinstance(item, dict):
                            col_before, col_arrow, col_after = st.columns([5, 1, 5])
                            with col_before:
                                st.error(f"❌ {item.get('original', '')}")
                            with col_arrow:
                                st.markdown("<h2 style='text-align:center;'>→</h2>", unsafe_allow_html=True)
                            with col_after:
                                st.success(f"✅ {item.get('suggested', '')}")
                        else:
                            st.markdown(f"- {item}")
                
                # --- Quantification Gaps ---
                quant_gaps = analysis_results.get("quantification_gaps", [])
                if quant_gaps:
                    st.markdown("---")
                    st.header("📏 Quantification Gaps")
                    st.caption("These bullet points lack metrics. Add numbers to make your impact measurable.")
                    for gap in quant_gaps:
                        st.warning(f"⚠️ {gap}")
                
                # --- Formatting Issues ---
                fmt_issues = analysis_results.get("formatting_issues", [])
                if fmt_issues:
                    st.markdown("---")
                    st.header("📐 Formatting Issues")
                    for issue in fmt_issues:
                        st.info(f"ℹ️ {issue}")
                
                # --- Stray Artifacts (deterministic — no LLM) ---
                if artifact_findings:
                    st.markdown("---")
                    st.header("🔍 Stray Artifacts & Leftover Placeholders")
                    st.caption("Found by scanning your resume text directly — these are exact locations, not AI guesses.")
                    for item in artifact_findings:
                        line_num = item['line_number']
                        with st.expander(f"📍 Line {line_num} — `{item['matched_text']}`", expanded=True):
                            st.markdown(f"**Line {line_num}:** `{item['line_text']}`")
                            st.markdown(f"**Found:** `{item['matched_text']}`")
                            st.markdown(f"**Problem:** {item['issue']}")
                
                # --- Consistency Issues ---
                consistency = analysis_results.get("consistency_issues", [])
                if consistency:
                    st.markdown("---")
                    st.header("⚖️ Internal Consistency Issues")
                    st.caption("Contradictions or mismatches across different sections of your resume.")
                    for item in consistency:
                        st.error(f"**{item.get('sections_involved', '')}**")
                        st.markdown(f"🔸 **Issue:** {item.get('issue', '')}")
                        st.markdown(f"🔹 **Suggestion:** {item.get('suggestion', '')}")
                        st.markdown("")
                
                # --- ATS Readiness Breakdown ---
                ats_info = analysis_results.get("ats_readiness", {})
                if ats_info:
                    st.markdown("---")
                    st.header("🤖 ATS Readiness Breakdown")
                    if ats_info.get("score_breakdown"):
                        st.write(ats_info["score_breakdown"])
                    
                    ats_col1, ats_col2 = st.columns(2)
                    with ats_col1:
                        st.subheader("⚠️ ATS Risks")
                        for risk in ats_info.get("risks", []):
                            st.warning(f"{risk}")
                    with ats_col2:
                        st.subheader("💡 ATS Suggestions")
                        for sug in ats_info.get("suggestions", []):
                            st.success(f"{sug}")
                
                # --- Missing Sections ---
                missing = analysis_results.get("missing_sections", [])
                if missing:
                    st.markdown("---")
                    st.header("📋 Missing Sections")
                    for section in missing:
                        st.warning(f"⚠️ Consider adding: **{section}**")
                
                # --- ATS Job Fit (when JD is provided) ---
                if job_description:
                    st.markdown("---")
                    st.header("🎯 ATS Job Fit Analysis")
                    ats_results = score_ats(resume_text, job_description)
                    
                    st.metric(label="ATS Job Match Score", value=f"{ats_results.get('ats_score', 0)}/100")
                    
                    st.subheader("Match Overview")
                    st.write(ats_results.get("keyword_density_issues", ats_results.get("match_overview", "")))
                    
                    col_c, col_d = st.columns(2)
                    with col_c:
                        st.subheader("✅ Matched Keywords")
                        for kw in ats_results.get("keyword_matches", []):
                            st.markdown(f"- {kw}")
                    with col_d:
                        st.subheader("❌ Missing Keywords")
                        for kw in ats_results.get("missing_keywords", []):
                            st.markdown(f"- {kw}")
                            
                    st.subheader("📝 Recommendations")
                    for rec in ats_results.get("recommendations", []):
                        st.markdown(f"- {rec}")
                        
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
