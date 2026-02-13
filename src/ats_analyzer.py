"""ATS Analyzer using Kimi API for holistic resume review."""

import os
import json
import httpx
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


KIMI_API_BASE = "https://api.moonshot.cn/v1"


@dataclass
class SectionScore:
    name: str
    score: int  # 0-100
    feedback: str
    improvements: List[str] = field(default_factory=list)


@dataclass
class KeywordAnalysis:
    found: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    repeated: List[Dict[str, Any]] = field(default_factory=list)  # word: count, suggestion


@dataclass
class ATSReport:
    overall_score: int
    summary: str
    sections: List[SectionScore]
    keywords: KeywordAnalysis
    action_verbs: Dict[str, Any]
    quantification: Dict[str, Any]
    formatting: Dict[str, Any]
    readability: Dict[str, Any]
    top_priorities: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_score": self.overall_score,
            "summary": self.summary,
            "sections": [
                {
                    "name": s.name,
                    "score": s.score,
                    "feedback": s.feedback,
                    "improvements": s.improvements
                }
                for s in self.sections
            ],
            "keywords": {
                "found": self.keywords.found,
                "missing": self.keywords.missing,
                "repeated": self.keywords.repeated
            },
            "action_verbs": self.action_verbs,
            "quantification": self.quantification,
            "formatting": self.formatting,
            "readability": self.readability,
            "top_priorities": self.top_priorities,
            "metadata": self.metadata
        }


async def analyze_resume(
    resume_text: str,
    job_description: Optional[str] = None,
    api_key: Optional[str] = None
) -> ATSReport:
    """
    Analyze resume using Kimi API.

    Args:
        resume_text: Plain text of the resume
        job_description: Optional job description to compare against
        api_key: Kimi API key (falls back to env var KIMI_API_KEY)

    Returns:
        ATSReport with scores and actionable insights
    """
    api_key = api_key or os.getenv("KIMI_API_KEY")
    if not api_key:
        raise ValueError("Kimi API key required. Set KIMI_API_KEY env var or pass api_key.")

    mode = "job-specific" if job_description else "general"

    system_prompt = """You are an expert ATS (Applicant Tracking System) analyzer and professional resume reviewer with deep knowledge of:
- How Fortune 500 companies screen resumes
- Industry-specific keyword optimization
- Action verb usage and impact statements
- Quantified achievements and metrics
- Resume structure and formatting for ATS compatibility
- Readability and scannability best practices

You provide holistic, honest feedback that helps candidates improve their chances of getting interviews. Be specific, actionable, and constructive."""

    user_prompt = f"""Analyze the following resume{' against the provided job description' if job_description else ''} and provide a comprehensive ATS review.

## RESUME:
```
{resume_text}
```

{'## JOB DESCRIPTION:' if job_description else ''}
{'```' if job_description else ''}
{job_description if job_description else ''}
{'```' if job_description else ''}

## ANALYSIS REQUIREMENTS:

Provide a JSON response with the following structure:

```json
{{
  "overall_score": <0-100>,
  "summary": "2-3 sentence holistic assessment",
  "sections": [
    {{
      "name": "Contact/Header|Professional Summary|Experience|Education|Projects|Skills",
      "score": <0-100>,
      "feedback": "Detailed feedback on this section",
      "improvements": ["specific actionable improvement 1", "improvement 2", ...]
    }}
  ],
  "keywords": {{
    "found": ["keyword1", "keyword2", ...],
    "missing": ["important missing keyword1", ...],
    "repeated": [
      {{"word": "overused word", "count": 5, "suggestion": "use synonyms like X, Y, Z"}}
    ]
  }},
  "action_verbs": {{
    "strong_verbs_used": ["Developed", "Architected", ...],
    "weak_verbs_found": ["Helped", "Assisted", ...],
    "recommendations": ["Replace 'Helped' with 'Drove' or 'Spearheaded'", ...]
  }},
  "quantification": {{
    "metrics_found": ["40-50% performance gains", "85.02% accuracy", ...],
    "missing_metrics_areas": ["Experience at Memfold AI lacks user impact numbers", ...],
    "recommendations": ["Add team size for projects", "Add % improvement metrics", ...]
  }},
  "formatting": {{
    "ats_compatible": true|false,
    "issues": ["Tables detected that may confuse ATS", ...],
    "strengths": ["Clean bullet points", "Consistent structure"]
  }},
  "readability": {{
    "bullet_length": "good|too_long|too_short",
    "avg_words_per_bullet": <number>,
    "scannability_score": <0-100>,
    "issues": ["Bullets are too dense", ...]
  }},
  "top_priorities": [
    "1. Most important fix - highest impact",
    "2. Second priority",
    "3. Third priority",
    ...
  ]
}}
```

Analysis Mode: {mode}

If job description provided, focus on:
- Keyword matching (missing critical skills)
- Experience alignment
- Tailoring opportunities

For general analysis, focus on:
- Universal best practices
- Industry standards
- Overall presentation quality

Be honest and specific. Prioritize actionable insights over generic praise."""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KIMI_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "kimi-latest",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            },
            timeout=120.0
        )

        response.raise_for_status()
        data = response.json()

        # Parse the JSON response
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)

        # Build ATSReport from parsed JSON
        sections = [
            SectionScore(
                name=s["name"],
                score=s["score"],
                feedback=s["feedback"],
                improvements=s.get("improvements", [])
            )
            for s in result.get("sections", [])
        ]

        keywords = KeywordAnalysis(
            found=result.get("keywords", {}).get("found", []),
            missing=result.get("keywords", {}).get("missing", []),
            repeated=result.get("keywords", {}).get("repeated", [])
        )

        return ATSReport(
            overall_score=result.get("overall_score", 0),
            summary=result.get("summary", ""),
            sections=sections,
            keywords=keywords,
            action_verbs=result.get("action_verbs", {}),
            quantification=result.get("quantification", {}),
            formatting=result.get("formatting", {}),
            readability=result.get("readability", {}),
            top_priorities=result.get("top_priorities", []),
            metadata={
                "model": data.get("model", "unknown"),
                "mode": mode
            }
        )


async def quick_keyword_scan(resume_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick scan for keywords and repetition issues.
    Faster than full analysis.
    """
    api_key = api_key or os.getenv("KIMI_API_KEY")
    if not api_key:
        raise ValueError("Kimi API key required.")

    prompt = f"""Quick scan this resume for keyword issues.

Resume:
```
{resume_text}
```

Return JSON:
{{
  "overused_words": [{{"word": "X", "count": N, "alternatives": ["Y", "Z"]}}],
  "weak_verbs": ["helped", "assisted"],
  "strong_alternatives": {{"helped": ["Drove", "Delivered"], "assisted": ["Supported", "Enabled"]}},
  "skill_gaps": ["missing modern framework", ...]
}}"""

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KIMI_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "kimi-latest",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            },
            timeout=60.0
        )

        response.raise_for_status()
        data = response.json()
        return json.loads(data["choices"][0]["message"]["content"])
