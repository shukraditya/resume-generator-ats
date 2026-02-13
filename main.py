"""FastAPI web application for Resume Converter + ATS Analyzer."""

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
from src.cache import (
    get_cache_key,
    get_cached_pdf,
    get_cached_latex,
    get_cached_ats,
    cache_result,
    get_cache_status
)

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
    """Home page with upload form."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/convert")
async def convert_resume(
    request: Request,
    resume_text: str = Form(""),
    resume_file: Optional[UploadFile] = File(None)
):
    """Convert markdown resume to LaTeX and PDF (cached)."""
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
        # Generate cache key
        cache_key = get_cache_key(resume_text)
        cache_info = get_cache_status(cache_key)

        # Check cache for LaTeX
        latex_content = get_cached_latex(cache_key)
        if latex_content is None:
            # Parse markdown and generate LaTeX
            resume_data = parse_markdown(resume_text)
            latex_content = generate_full_latex(resume_data)

        # Check cache for PDF
        pdf_bytes = get_cached_pdf(cache_key)
        if pdf_bytes is None:
            # Generate PDF
            pdf_bytes = generate_pdf_bytes(latex_content)
            # Cache the result
            cache_result(cache_key, pdf=pdf_bytes, latex=latex_content)

        # Determine contact name for display
        resume_data = parse_markdown(resume_text)

        # Generate filename for download
        base_name = get_output_filename(original_name)
        download_filename = f"{base_name}.pdf"

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "latex_preview": latex_content[:2000] + "..." if len(latex_content) > 2000 else latex_content,
                "download_filename": download_filename,
                "contact_name": resume_data.contact.name or "Unknown",
                "cache_status": "HIT" if cache_info.get('has_pdf') else "MISS"
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
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
        # Generate cache key
        cache_key = get_cache_key(resume_text)

        # Check cache first
        pdf_bytes = get_cached_pdf(cache_key)
        latex_content = get_cached_latex(cache_key)
        cache_hit = pdf_bytes is not None

        if pdf_bytes is None:
            # Parse and generate
            resume_data = parse_markdown(resume_text)
            latex_content = generate_full_latex(resume_data)
            pdf_bytes = generate_pdf_bytes(latex_content)
            # Cache result
            cache_result(cache_key, pdf=pdf_bytes, latex=latex_content)

        # Generate download filename
        base_name = get_output_filename(original_name)
        download_filename = f"{base_name}.pdf"

        # Stream PDF response
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "X-Cache": "HIT" if cache_hit else "MISS"
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
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
    """Analyze resume with ATS agent (cached)."""
    # Get content from file or text
    if resume_file and resume_file.filename:
        content = await resume_file.read()
        resume_text = content.decode("utf-8")

    if not resume_text.strip():
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Please provide resume text or upload a file."}
        )

    # Check for API key
    if not os.getenv("KIMI_API_KEY"):
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "KIMI_API_KEY not set. Please set your Kimi API key."}
        )

    try:
        # Generate cache key
        cache_key = get_cache_key(resume_text)

        # Convert markdown to plain text for analysis
        plain_text = markdown.markdown(resume_text)
        plain_text = re.sub(r'<[^>]+>', '', plain_text)

        # Check cache for ATS analysis
        cached_ats = get_cached_ats(cache_key)
        cache_hit = cached_ats is not None

        if cached_ats is not None:
            # Use cached report
            report = ATSReport(**cached_ats)
        else:
            # Run analysis
            job_desc = job_description if analysis_mode == "job_match" and job_description.strip() else None
            report = await analyze_resume(plain_text, job_desc)

            # Cache the report (convert to dict for storage)
            ats_dict = report.to_dict()
            cache_result(cache_key, ats=ats_dict)

        return templates.TemplateResponse(
            "analysis.html",
            {
                "request": request,
                "report": report,
                "report_json": report.to_dict(),
                "mode": "job-match" if (analysis_mode == "job_match" and job_description.strip()) else "standalone",
                "cache_status": "HIT" if cache_hit else "MISS"
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": f"Analysis failed: {str(e)}"}
        )


@app.get("/download-latex")
async def download_latex(
    resume_text: str = ""
):
    """Download LaTeX source for a given resume text."""
    if not resume_text.strip():
        return JSONResponse({"error": "No resume text provided"}, status_code=400)

    cache_key = get_cache_key(resume_text)
    latex_content = get_cached_latex(cache_key)

    if latex_content is None:
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


@app.get("/cache-status")
async def cache_status_endpoint():
    """Get cache statistics (for monitoring)."""
    from src.cache import get_cache_stats
    return get_cache_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
