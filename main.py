"""FastAPI web application for Resume Converter + ATS Analyzer."""

import base64
import io
import os
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, UploadFile, File, Request, Header
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import markdown

from src.md_parser import parse_markdown
from src.latex_generator import generate_full_latex
from src.pdf_generator import generate_pdf_bytes
from src.ats_analyzer import analyze_resume, ATSReport
from src.ats_improver import generate_latex_improvements
from src.diff_utils import apply_unified_diff, apply_suggestions_sequential
from src.models import LaTeXSuggestion

# Create FastAPI app
app = FastAPI(title="Resume Converter + ATS Analyzer", version="2.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")


def get_output_filename(original_name: str) -> str:
    """Generate output filename in format: original_name+jake.pdf"""
    base = Path(original_name).stem
    return f"{base}+jake"


def normalize_resume_text(resume_text: str) -> str:
    """Normalize resume text for consistent hashing."""
    return resume_text.strip().lower().replace('\r\n', '\n')


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Landing page with two options."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/convert", response_class=HTMLResponse)
async def convert_page(request: Request):
    """LaTeX/PDF conversion page."""
    return templates.TemplateResponse("convert.html", {"request": request})


@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    """ATS analysis page."""
    return templates.TemplateResponse("analyze_form.html", {"request": request})


@app.post("/convert")
async def convert_resume(
    request: Request,
    resume_text: str = Form(""),
    resume_file: Optional[UploadFile] = File(None)
):
    """Convert markdown resume to LaTeX and PDF."""
    # Get content from file or text
    if resume_file and resume_file.filename:
        content = await resume_file.read()
        resume_text = content.decode("utf-8")
        original_name = resume_file.filename
    else:
        original_name = "resume.md"

    if not resume_text.strip():
        return templates.TemplateResponse(
            "convert.html",
            {"request": request, "error": "Please provide resume text or upload a file."}
        )

    try:
        # Parse markdown and generate LaTeX
        resume_data = parse_markdown(resume_text)
        latex_content = generate_full_latex(resume_data)

        # Generate PDF
        pdf_bytes = generate_pdf_bytes(latex_content)

        # Encode PDF as base64 for direct download
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        # Generate filename for download
        base_name = get_output_filename(original_name)
        download_filename = f"{base_name}.pdf"

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "latex_preview": latex_content[:2000] + "..." if len(latex_content) > 2000 else latex_content,
                "full_latex": latex_content,
                "download_filename": download_filename,
                "contact_name": resume_data.contact.name or "Unknown",
                "pdf_base64": pdf_base64
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "convert.html",
            {"request": request, "error": f"Conversion failed: {str(e)}"}
        )


@app.post("/convert-stream")
async def convert_resume_stream(
    request: Request,
    resume_text: str = Form(""),
    resume_file: Optional[UploadFile] = File(None)
):
    """Stream PDF directly to browser without saving to disk."""
    # Get content from file or text
    if resume_file and resume_file.filename:
        content = await resume_file.read()
        resume_text = content.decode("utf-8")
        original_name = resume_file.filename
    else:
        original_name = "resume.md"

    if not resume_text.strip():
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Please provide resume text or upload a file."}
        )

    try:
        # Parse and generate fresh PDF
        resume_data = parse_markdown(resume_text)
        latex_content = generate_full_latex(resume_data)
        pdf_bytes = generate_pdf_bytes(latex_content)

        # Generate download filename
        base_name = get_output_filename(original_name)
        download_filename = f"{base_name}.pdf"

        # Stream PDF response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"'
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "convert.html",
            {"request": request, "error": f"Conversion failed: {str(e)}"}
        )


@app.post("/analyze")
async def analyze_resume_endpoint(
    request: Request,
    resume_text: str = Form(""),
    resume_file: Optional[UploadFile] = File(None),
    job_description: str = Form(""),
    analysis_mode: str = Form("standalone")
):
    """Analyze resume with ATS agent."""
    # Get content from file or text
    if resume_file and resume_file.filename:
        content = await resume_file.read()
        resume_text = content.decode("utf-8")

    if not resume_text.strip():
        return templates.TemplateResponse(
            "analyze_form.html",
            {"request": request, "error": "Please provide resume text or upload a file."}
        )

    # Check for API key
    if not os.getenv("KIMI_API_KEY"):
        return templates.TemplateResponse(
            "analyze_form.html",
            {"request": request, "error": "KIMI_API_KEY not set. Please set your Kimi API key."}
        )

    try:
        # Convert markdown to plain text for analysis
        plain_text = markdown.markdown(resume_text)
        plain_text = re.sub(r'<[^>]+>', '', plain_text)

        # Run analysis
        job_desc = job_description if analysis_mode == "job_match" and job_description.strip() else None
        report = await analyze_resume(plain_text, job_desc)

        return templates.TemplateResponse(
            "analysis.html",
            {
                "request": request,
                "report": report,
                "report_json": report.to_dict(),
                "mode": "job-match" if (analysis_mode == "job_match" and job_description.strip()) else "standalone"
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "analyze_form.html",
            {"request": request, "error": f"Analysis failed: {str(e)}"}
        )


@app.get("/download-latex")
async def download_latex(
    resume_text: str = ""
):
    """Download LaTeX source for a given resume text."""
    if not resume_text.strip():
        return JSONResponse({"error": "No resume text provided"}, status_code=400)

    # Generate on the fly
    try:
        resume_data = parse_markdown(resume_text)
        latex_content = generate_full_latex(resume_data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    return StreamingResponse(
        io.BytesIO(latex_content.encode('utf-8')),
        media_type="text/x-tex",
        headers={
            "Content-Disposition": 'attachment; filename="resume+jake.tex"'
        }
    )


# ============ EDITOR ENDPOINTS ============

@app.get("/editor", response_class=HTMLResponse)
async def editor_page_get(
    request: Request,
    resume_text: str = "",
    latex_content: str = ""
):
    """Overleaf-like editor with split-pane LaTeX editing (GET)."""
    return await render_editor(request, resume_text, latex_content)


@app.post("/editor", response_class=HTMLResponse)
async def editor_page_post(
    request: Request,
    resume_text: str = Form(""),
    latex_content: str = Form("")
):
    """Overleaf-like editor with split-pane LaTeX editing (POST)."""
    return await render_editor(request, resume_text, latex_content)


async def render_editor(request: Request, resume_text: str, latex_content: str):
    """Render the editor page with LaTeX content."""
    # If latex_content provided, use it directly
    # Otherwise, generate from resume_text
    if not latex_content and resume_text:
        try:
            resume_data = parse_markdown(resume_text)
            latex_content = generate_full_latex(resume_data)
        except Exception as e:
            return templates.TemplateResponse(
                "convert.html",
                {"request": request, "error": f"Failed to generate LaTeX: {str(e)}"}
            )

    if not latex_content:
        # Default template for empty editor
        latex_content = r"""\documentclass[letterpaper,11pt]{article}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{hyperref}

\begin{document}
% Paste your LaTeX here
\end{document}"""

    # Generate initial PDF
    try:
        pdf_bytes = generate_pdf_bytes(latex_content)
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    except Exception as e:
        pdf_base64 = ""

    return templates.TemplateResponse(
        "editor.html",
        {
            "request": request,
            "latex_content": latex_content,
            "pdf_base64": pdf_base64
        }
    )


@app.post("/editor/compile")
async def editor_compile(
    request: Request,
    latex_content: str = Form("")
):
    """Compile LaTeX to PDF for editor preview."""
    if not latex_content.strip():
        return JSONResponse({
            "success": False,
            "error": "No LaTeX content provided",
            "pdf_base64": None
        })

    try:
        pdf_bytes = generate_pdf_bytes(latex_content)
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        return JSONResponse({
            "success": True,
            "pdf_base64": pdf_base64,
            "error": None
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e),
            "pdf_base64": None
        })


@app.post("/editor/export")
async def editor_export(
    latex_content: str = Form("")
):
    """Export compiled PDF from editor."""
    if not latex_content.strip():
        return JSONResponse({"error": "No LaTeX content"}, status_code=400)

    try:
        pdf_bytes = generate_pdf_bytes(latex_content)

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="resume+jake.pdf"'
            }
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ============ IMPROVE ENDPOINTS ============

@app.get("/improve", response_class=HTMLResponse)
async def improve_page_get(
    request: Request,
    resume_text: str = "",
    latex_content: str = ""
):
    """ATS improvements page with git diff suggestions (GET)."""
    return await render_improve(request, resume_text, latex_content)


@app.post("/improve", response_class=HTMLResponse)
async def improve_page_post(
    request: Request,
    resume_text: str = Form(""),
    latex_content: str = Form("")
):
    """ATS improvements page with git diff suggestions (POST)."""
    return await render_improve(request, resume_text, latex_content)


async def render_improve(request: Request, resume_text: str, latex_content: str):
    """Render the improve page."""
    if not latex_content and resume_text:
        try:
            resume_data = parse_markdown(resume_text)
            latex_content = generate_full_latex(resume_data)
        except Exception as e:
            return templates.TemplateResponse(
                "analyze_form.html",
                {"request": request, "error": f"Failed to process resume: {str(e)}"}
            )

    if not latex_content:
        return templates.TemplateResponse(
            "analyze_form.html",
            {"request": request, "error": "Please provide resume text first."}
        )

    return templates.TemplateResponse(
        "improve.html",
        {
            "request": request,
            "resume_text": resume_text,
            "latex_content": latex_content
        }
    )


@app.post("/improve")
async def improve_generate(
    request: Request,
    resume_text: str = Form(""),
    latex_content: str = Form(""),
    job_description: str = Form("")
):
    """Generate ATS improvement suggestions as git diffs."""
    if not latex_content or not resume_text:
        return JSONResponse({
            "error": "Both resume_text and latex_content are required"
        }, status_code=400)

    if not os.getenv("KIMI_API_KEY"):
        return JSONResponse({
            "error": "KIMI_API_KEY not set"
        }, status_code=500)

    try:
        # Get ATS analysis
        import markdown
        plain_text = markdown.markdown(resume_text)
        plain_text = re.sub(r'<[^>]+>', '', plain_text)

        ats_report = await analyze_resume(
            plain_text,
            job_description if job_description.strip() else None
        )

        # Generate LaTeX improvements
        improvements = await generate_latex_improvements(
            resume_text=resume_text,
            latex_content=latex_content,
            ats_report=ats_report,
            job_description=job_description if job_description.strip() else None
        )

        return JSONResponse({
            "success": True,
            "suggestions": [s.to_dict() for s in improvements.suggestions],
            "overall_score": improvements.overall_score,
            "target_score": improvements.target_score
        })

    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)


@app.post("/improve/apply")
async def improve_apply(
    request: Request,
    latex_content: str = Form(""),
    diff: str = Form("")
):
    """Apply a single diff to LaTeX content."""
    if not latex_content or not diff:
        return JSONResponse({
            "error": "Both latex_content and diff are required"
        }, status_code=400)

    success, updated_latex, error = apply_unified_diff(latex_content, diff)

    return JSONResponse({
        "success": success,
        "updated_latex": updated_latex,
        "error": error
    })


@app.post("/improve/apply-all")
async def improve_apply_all(
    request: Request,
    latex_content: str = Form(""),
    suggestions: str = Form("[]")  # JSON array of suggestion objects
):
    """Apply all non-conflicting suggestions."""
    if not latex_content:
        return JSONResponse({
            "error": "latex_content is required"
        }, status_code=400)

    try:
        import json
        suggestion_list = json.loads(suggestions)

        # Convert to LaTeXSuggestion objects
        suggestions_objs = [LaTeXSuggestion(**s) for s in suggestion_list]

        # Apply sequentially
        updated_latex, results = apply_suggestions_sequential(
            latex_content,
            suggestions_objs
        )

        return JSONResponse({
            "success": True,
            "updated_latex": updated_latex,
            "applied_count": sum(results),
            "total_count": len(results)
        })

    except Exception as e:
        return JSONResponse({
            "error": str(e)
        }, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
