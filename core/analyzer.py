import json
import os
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from pathlib import Path
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from absolute path
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    max_tokens=2048,
    groq_api_key=os.getenv("GROQ_API_KEY"),
)

# Separate LLM instance with higher temperature for creative rewriting
llm_creative = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.5,
    max_tokens=4096,
    groq_api_key=os.getenv("GROQ_API_KEY"),
)


def _load_prompt(filename: str) -> str:
    """Load prompt template from the prompts/ directory."""
    return (Path(__file__).parent.parent / "prompts" / filename).read_text()


def _clean_json_response(text: str) -> str:
    """Strip markdown fences and whitespace from LLM JSON responses."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    return text.strip()


def analyze_resume(resume_text: str) -> dict:
    """Run general resume analysis and return structured JSON results."""
    prompt = PromptTemplate.from_template(_load_prompt("analyze.txt"))
    chain = prompt | llm
    response = chain.invoke({"resume_text": resume_text})
    cleaned = _clean_json_response(response.content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "overall_score": 0,
            "summary": "Analysis failed — could not parse AI response.",
            "strengths": [],
            "weaknesses": [],
            "missing_sections": [],
            "skills_identified": {"technical": [], "soft": []},
            "quantification_gaps": [],
            "action_verb_issues": [],
            "formatting_issues": [],
            "top_3_improvements": ["Try re-analyzing your resume."],
            "_raw_response": cleaned,
        }


def score_ats(resume_text: str, job_description: str) -> dict:
    """Score resume ATS compatibility against a job description."""
    prompt = PromptTemplate.from_template(_load_prompt("ats_score.txt"))
    chain = prompt | llm
    response = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description,
    })
    cleaned = _clean_json_response(response.content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "ats_score": 0,
            "keyword_matches": [],
            "missing_keywords": [],
            "keyword_density_issues": "Could not parse response.",
            "formatting_ats_risks": [],
            "recommendations": [],
            "_raw_response": cleaned,
        }


def tailor_resume(resume_text: str, job_description: str) -> str:
    """Rewrite resume optimized for a specific job description."""
    prompt = PromptTemplate.from_template(_load_prompt("tailor.txt"))
    chain = prompt | llm_creative  # Higher temperature for natural rewrites
    response = chain.invoke({
        "resume_text": resume_text,
        "job_description": job_description,
    })
    return response.content
