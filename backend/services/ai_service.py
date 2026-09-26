"""
AI classification service.

Priority order:
  1. Groq API (free tier, fast, cloud — needs GROQ_API_KEY)
  2. Ollama (local — needs ollama serve, optional)
  3. Rule-based (always works, no dependencies)

AI is ENRICHMENT ONLY.
Failure at any level never blocks email storage or display.
"""
import re
import json
import logging
import httpx
import os
from typing import Dict, Any, List, Optional

from supabase import Client
from .db import upsert_ai_analysis

logger = logging.getLogger(__name__)

GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
GROQ_BASE     = "https://api.groq.com/openai/v1"
GROQ_MODEL    = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")   # free, very fast

OLLAMA_BASE   = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Prompt (shared) ───────────────────────────────────────────────────────────

CLASSIFY_PROMPT = """\
Classify this email into exactly ONE category and respond with JSON only.

Categories: jobs, competitions, tech, reddit, newsletters, college, personal, other

- jobs: job postings, interview invites, recruiter messages, application status
- competitions: hackathons, coding contests, CTFs, challenges
- tech: GitHub, AI/ML news, cybersecurity, developer tools, tech articles
- reddit: Reddit notifications, upvotes, comment replies
- newsletters: newsletters, marketing, promotional, unsubscribe emails
- college: university/college announcements, courses, exams, campus
- personal: real person wrote this (not automated)
- other: anything else

Email:
Subject: {subject}
From: {sender}
Body preview: {snippet}

JSON response format:
{{"category":"<category>","priority":"high|medium|low","action_required":true|false,"summary":"<one sentence max>","keywords":["kw1","kw2","kw3"]}}"""


# ── Groq classifier ───────────────────────────────────────────────────────────

async def classify_with_groq(
    subject: str, sender_email: str, snippet: str
) -> Optional[Dict[str, Any]]:
    if not GROQ_API_KEY:
        return None

    prompt = CLASSIFY_PROMPT.format(
        subject=subject[:200],
        sender=sender_email[:100],
        snippet=snippet[:500],
    )

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{GROQ_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 200,
                    "response_format": {"type": "json_object"},
                },
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            parsed["model"] = f"groq/{GROQ_MODEL}"
            parsed["confidence"] = 0.92
            return parsed
    except Exception as e:
        logger.warning(f"Groq classify failed: {e}")
        return None


# ── Ollama classifier (optional local fallback) ───────────────────────────────

async def classify_with_ollama(
    subject: str, sender_email: str, snippet: str, model: str
) -> Optional[Dict[str, Any]]:
    prompt = CLASSIFY_PROMPT.format(
        subject=subject[:200],
        sender=sender_email[:100],
        snippet=snippet[:500],
    )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
            )
            r.raise_for_status()
            response_text = r.json().get("response", "{}")
            parsed = json.loads(response_text)
            parsed["model"] = f"ollama/{model}"
            parsed["confidence"] = 0.88
            return parsed
    except Exception as e:
        logger.warning(f"Ollama classify failed (not running?): {e}")
        return None


# ── Rule-based fallback (always works, zero dependencies) ─────────────────────

RULES: List[Dict[str, Any]] = [
    {
        "category": "reddit",
        "sender_patterns": [r"noreply@reddit\.com", r"@reddit\.com"],
        "patterns": [r"reddit\.com", r"\br/\w+", r"\bu/\w+", r"upvot", r"subreddit"],
    },
    {
        "category": "jobs",
        "sender_patterns": [r"linkedin\.com", r"careers@", r"recruiting@", r"noreply@.*job"],
        "patterns": [
            r"\bjob\b", r"\bposition\b", r"\bopening\b", r"\brecruiter\b",
            r"\binterview\b", r"\bhiring\b", r"\binternship\b", r"\bapplication received\b",
        ],
    },
    {
        "category": "competitions",
        "sender_patterns": [r"devpost\.com", r"mlh\.io", r"hackerearth\.com", r"topcoder\.com"],
        "patterns": [
            r"\bhackathon\b", r"\bcompetition\b", r"\bcontest\b",
            r"\bctf\b", r"\bchallenge\b", r"\bsubmission deadline\b",
        ],
    },
    {
        "category": "tech",
        "sender_patterns": [r"github\.com", r"stackoverflow\.com", r"hackernews"],
        "patterns": [
            r"\bgithub\b", r"\bmachine learning\b", r"\bcybersecurity\b",
            r"\bopen.?source\b", r"\bvulnerability\b", r"\bprogramming\b",
            r"\bai\b", r"\bllm\b", r"\binfosec\b",
        ],
    },
    {
        "category": "college",
        "sender_patterns": [r"\.edu$", r"\.ac\.in$", r"university@", r"college@"],
        "patterns": [
            r"\buniversity\b", r"\bcollege\b", r"\bcampus\b",
            r"\bsemester\b", r"\bexam\b", r"\bcourse\b", r"\bassignment\b",
        ],
    },
    {
        "category": "newsletters",
        "sender_patterns": [r"newsletter@", r"digest@", r"substack\.com", r"mailchimp\.com"],
        "patterns": [
            r"\bunsubscribe\b", r"\bnewsletter\b", r"\bweekly digest\b", r"\bview in browser\b",
        ],
    },
]


def classify_rule_based(subject: str, body: str, sender_email: str) -> Dict[str, Any]:
    text = f"{subject} {body}".lower()
    sender = sender_email.lower()

    for rule in RULES:
        for sp in rule["sender_patterns"]:
            if re.search(sp, sender):
                return {"category": rule["category"], "confidence": 0.8, "model": "rule-based"}
        hits = sum(1 for p in rule["patterns"] if re.search(p, text))
        if hits >= 2:
            return {
                "category": rule["category"],
                "confidence": min(0.5 + hits * 0.1, 0.85),
                "model": "rule-based",
            }

    return {"category": "other", "confidence": 0.5, "model": "rule-based"}


# ── Main entry point ──────────────────────────────────────────────────────────

async def analyze_email_background(
    client: Client,
    email_id: str,
    email_data: Dict[str, Any],
    ollama_model: str = "llama3.2",
) -> None:
    """
    Classify one email and store result. Best-effort — caller handles exceptions.

    Order tried:
      1. Groq  (if GROQ_API_KEY is set)
      2. Ollama (if running locally)
      3. Rule-based (always)
    """
    subject      = email_data.get("subject") or ""
    sender_email = email_data.get("sender_email") or ""
    snippet      = (email_data.get("snippet") or email_data.get("body_text") or "")[:400]

    result = (
        await classify_with_groq(subject, sender_email, snippet)
        or await classify_with_ollama(subject, sender_email, snippet, ollama_model)
        or classify_rule_based(subject, email_data.get("body_text") or "", sender_email)
    )

    await upsert_ai_analysis(client, email_id, result)
