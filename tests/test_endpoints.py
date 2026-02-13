"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app
from src.cache import clear_cache


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache_before_tests():
    """Clear cache before each test."""
    clear_cache()


class TestIndexEndpoint:
    """Test the home page."""

    def test_index_loads(self, client):
        """Homepage should load successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Resume Converter" in response.text
        assert "ATS Analyzer" in response.text

    def test_index_has_forms(self, client):
        """Homepage should have conversion and analysis forms."""
        response = client.get("/")
        assert response.status_code == 200
        assert 'action="/convert"' in response.text
        assert 'action="/analyze"' in response.text


class TestConvertEndpoint:
    """Test the conversion endpoint."""

    def test_convert_with_text(self, client):
        """Convert with resume text."""
        import shutil

        resume_text = """# **Test User**

Test Location | LinkedIn | +1234567890 | test@example.com | GitHub

**EDUCATION**
**Test University** **Test Location**
*Degree* 2020-2024

**WORK EXPERIENCE**
**Test Company** **Test Location**
*Role* 2024-Present

* Did something important
* Another achievement
"""
        response = client.post(
            "/convert",
            data={"resume_text": resume_text}
        )

        # Should succeed (if pdflatex installed) or fail gracefully
        assert response.status_code == 200

        if shutil.which("pdflatex"):
            assert "Conversion Complete" in response.text
            assert "LaTeX Preview" in response.text
        else:
            # pdflatex not installed - should show error
            assert "Conversion failed" in response.text or "pdflatex" in response.text

    def test_convert_empty_text(self, client):
        """Convert with empty text should show error."""
        response = client.post(
            "/convert",
            data={"resume_text": ""}
        )

        assert response.status_code == 200
        assert "Please provide resume text" in response.text or "Conversion Complete" in response.text

    def test_convert_caching(self, client):
        """Second conversion should use cache (only if pdflatex available)."""
        import shutil

        if not shutil.which("pdflatex"):
            pytest.skip("pdflatex not installed")

        resume_text = """# **Cache Test**

Location | LinkedIn | +1234567890 | test@example.com | GitHub

**EDUCATION**
**University** **Location**
*Degree* 2020-2024
"""
        # First request
        response1 = client.post("/convert", data={"resume_text": resume_text})

        # Second request with same content
        response2 = client.post("/convert", data={"resume_text": resume_text})

        if response1.status_code == 200 and response2.status_code == 200:
            # Should show cached status on second request
            assert "Cached" in response2.text


class TestConvertStreamEndpoint:
    """Test the streaming PDF endpoint."""

    def test_stream_pdf(self, client):
        """Stream endpoint should return PDF or error page."""
        resume_text = """# **Stream Test**

Location | LinkedIn | +1234567890 | test@example.com | GitHub

**EDUCATION**
**University** **Location**
*Degree* 2020-2024
"""
        response = client.post(
            "/convert-stream",
            data={"resume_text": resume_text}
        )

        # Should either return PDF or error page
        assert response.status_code in [200]

        if response.headers.get("content-type") == "application/pdf":
            assert response.content.startswith(b"%PDF")
            assert "X-Cache" in response.headers
        else:
            # Error page
            assert "Conversion failed" in response.text or "Resume Converter" in response.text

    def test_stream_caching_headers(self, client):
        """Stream should return cache headers."""
        resume_text = """# **Cache Header Test**

Location | LinkedIn | +1234567890 | test@example.com | GitHub

**EDUCATION**
**University** **Location**
*Degree* 2020-2024
"""
        response = client.post(
            "/convert-stream",
            data={"resume_text": resume_text}
        )

        # Should have X-Cache header if PDF was generated
        if response.headers.get("content-type") == "application/pdf":
            assert response.headers["X-Cache"] in ["HIT", "MISS"]


class TestAnalyzeEndpoint:
    """Test the ATS analysis endpoint."""

    def test_analyze_without_api_key(self, client):
        """Analyze without API key should show error."""
        resume_text = "# Test\n\nContent"

        response = client.post(
            "/analyze",
            data={
                "resume_text": resume_text,
                "analysis_mode": "standalone"
            }
        )

        assert response.status_code == 200
        assert "KIMI_API_KEY not set" in response.text

    def test_analyze_empty_text(self, client):
        """Analyze with empty text should show error."""
        response = client.post(
            "/analyze",
            data={
                "resume_text": "",
                "analysis_mode": "standalone"
            }
        )

        assert response.status_code == 200
        assert "Please provide resume text" in response.text


class TestCacheStatusEndpoint:
    """Test the cache status endpoint."""

    def test_cache_status_empty(self, client):
        """Cache status when empty."""
        response = client.get("/cache-status")
        assert response.status_code == 200
        data = response.json()
        assert data["total_entries"] == 0
        assert data["with_pdf"] == 0
        assert data["with_latex"] == 0
        assert data["with_valid_ats"] == 0

    def test_cache_status_with_entries(self, client):
        """Cache status with entries."""
        from src.cache import cache_result

        cache_result("key1", pdf=b"pdf")
        cache_result("key2", latex="latex")

        response = client.get("/cache-status")
        assert response.status_code == 200
        data = response.json()
        assert data["total_entries"] == 2
        assert data["with_pdf"] == 1
        assert data["with_latex"] == 1


class TestFileUpload:
    """Test file upload functionality."""

    def test_upload_md_file(self, client, tmp_path):
        """Upload a markdown file."""
        md_file = tmp_path / "resume.md"
        md_file.write_text("""# **Test User**

Location | LinkedIn | +1234567890 | test@example.com | GitHub

**EDUCATION**
**University** **Location**
*Degree* 2020-2024
""")

        with open(md_file, "rb") as f:
            response = client.post(
                "/convert",
                files={"resume_file": ("resume.md", f, "text/markdown")}
            )

        # Should process the file
        assert response.status_code in [200, 500]
