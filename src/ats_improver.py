"""ATS Improver using Kimi API to suggest LaTeX improvements as git diffs."""

import os
import json
import uuid
import httpx
from typing import List, Optional, Dict, Any

from .models import LaTeXSuggestion, LaTeXImprovementResponse
from .ats_analyzer import analyze_resume, ATSReport


KIMI_API_BASE = "https://api.moonshot.cn/v1"


async def generate_latex_improvements(
    resume_text: str,
    latex_content: str,
    ats_report: ATSReport,
    job_description: Optional[str] = None,
    api_key: Optional[str] = None
) -> LaTeXImprovementResponse:
    """
    Generate LaTeX improvement suggestions based on ATS analysis.

    Args:
        resume_text: Original markdown/plain text resume
        latex_content: Current LaTeX content
        ats_report: The ATS analysis report
        job_description: Optional job description
        api_key: Kimi API key

    Returns:
        LaTeXImprovementResponse with suggestions as git diffs
    """
    api_key = api_key or os.getenv("KIMI_API_KEY")
    if not api_key:
        raise ValueError("Kimi API key required. Set KIMI_API_KEY env var or pass api_key.")

    system_prompt = """You are an expert ATS optimization specialist and professional resume writer.

Your task is to analyze a LaTeX resume and ATS analysis report, then suggest specific improvements as valid unified git diffs.

Rules for generating diffs:
1. Use proper unified diff format with --- a/resume.tex, +++ b/resume.tex, and @@ markers
2. Each suggestion should target ONE specific issue
3. Focus on: action verbs, quantification, keyword density, formatting clarity
4. Keep changes minimal and focused
5. Ensure the diff applies cleanly to the provided LaTeX

Priority areas based on ATS analysis:
- Replace weak verbs (Helped, Worked on, Assisted) with strong ones (Engineered, Architected, Delivered)
- Add quantification where missing (%, numbers, team sizes)
- Improve keyword density for missing terms
- Fix formatting that hurts ATS parsing

Response must be valid JSON with a "suggestions" array."""

    # Build context from ATS report
    weak_verbs = ats_report.action_verbs.get("weak_verbs_found", [])
    missing_keywords = ats_report.keywords.missing
    top_priorities = ats_report.top_priorities
    quant_issues = ats_report.quantification.get("missing_metrics_areas", [])

    user_prompt = f"""Analyze this LaTeX resume and ATS report. Generate 3-5 specific improvement suggestions as git diffs.

## CURRENT LATEX RESUME:
```latex
{latex_content}
```

## ATS ANALYSIS SUMMARY:
- Overall Score: {ats_report.overall_score}/100
- Weak Verbs Found: {weak_verbs}
- Missing Keywords: {missing_keywords[:10]}
- Top Priorities:
{chr(10).join(f"  - {p}" for p in top_priorities[:3])}

## QUANTIFICATION ISSUES:
{chr(10).join(f"  - {q}" for q in quant_issues[:3]) if quant_issues else "  - Need to add metrics to experience bullets"}

{job_description and f'''## JOB DESCRIPTION (for targeting):
```
{job_description}
```
''' or ''}

Generate suggestions that:
1. Replace weak verbs with strong action verbs in \\resumeItem lines
2. Add quantification (%, numbers, scale) to achievement bullets
3. Include missing keywords naturally in existing content
4. Improve section clarity for ATS parsing

Response format:
```json
{{
  "suggestions": [
    {{
      "description": "Brief description of the improvement",
      "target_section": "Experience|Education|Projects|Skills",
      "priority": 1-5 (1=highest, 5=lowest),
      "diff": "--- a/resume.tex\\n+++ b/resume.tex\\n@@ -10,5 +10,5 @@...",
      "reason": "Why this improves ATS score"
    }}
  ],
  "overall_score": {ats_report.overall_score},
  "target_score": 85
}}
```

Ensure each diff:
- Uses proper unified diff syntax (---, +++, @@ headers)
- Targets specific \\resumeItem or section lines
- Is minimal and focused on one change
- Can be applied programmatically"""

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

        # Parse JSON response
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)

        # Build suggestions
        suggestions = []
        for s in result.get("suggestions", []):
            suggestion = LaTeXSuggestion(
                id=str(uuid.uuid4())[:8],
                description=s.get("description", ""),
                target_section=s.get("target_section", "General"),
                priority=s.get("priority", 3),
                diff=s.get("diff", ""),
                reason=s.get("reason", "")
            )
            suggestions.append(suggestion)

        # Sort by priority (lower = higher priority)
        suggestions.sort(key=lambda x: x.priority)

        return LaTeXImprovementResponse(
            suggestions=suggestions,
            overall_score=result.get("overall_score", ats_report.overall_score),
            target_score=result.get("target_score", min(ats_report.overall_score + 15, 95))
        )


async def quick_latex_improvements(
    latex_content: str,
    quick_fixes: List[Dict[str, str]],
    api_key: Optional[str] = None
) -> List[LaTeXSuggestion]:
    """
    Generate quick improvements based on specific fix requests.

    Args:
        latex_content: Current LaTeX content
        quick_fixes: List of fix requests, e.g., [{"type": "verb", "from": "Helped", "to": "Engineered"}]
        api_key: Kimi API key

    Returns:
        List of LaTeXSuggestion objects
    """
    api_key = api_key or os.getenv("KIMI_API_KEY")
    if not api_key:
        raise ValueError("Kimi API key required.")

    fixes_str = json.dumps(quick_fixes, indent=2)

    prompt = f"""Generate minimal git diffs for these specific improvements:

## CURRENT LATEX:
```latex
{latex_content[:3000]}
```

## REQUESTED FIXES:
```json
{fixes_str}
```

For each fix, generate a unified diff that targets the specific line to change.
Focus on \\resumeItem lines.

Response format:
```json
{{
  "suggestions": [
    {{
      "description": "Replace weak verb",
      "target_section": "Experience",
      "priority": 1,
      "diff": "--- a/resume.tex\\n+++ b/resume.tex\\n@@ -45,3 +45,3 @@...",
      "reason": "Stronger action verb"
    }}
  ]
}}
```"""

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
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)

        suggestions = []
        for s in result.get("suggestions", []):
            suggestion = LaTeXSuggestion(
                id=str(uuid.uuid4())[:8],
                description=s.get("description", ""),
                target_section=s.get("target_section", "General"),
                priority=s.get("priority", 3),
                diff=s.get("diff", ""),
                reason=s.get("reason", "")
            )
            suggestions.append(suggestion)

        return suggestions
