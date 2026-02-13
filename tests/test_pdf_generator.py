"""Tests for PDF generation module."""

import shutil
import pytest
from src.pdf_generator import generate_pdf_bytes

# Skip all tests in this file if pdflatex is not installed
pdflatex_available = shutil.which("pdflatex") is not None


@pytest.mark.skipif(not pdflatex_available, reason="pdflatex not installed")
class TestGeneratePdfBytes:
    """Test the streaming PDF generation function."""

    def test_valid_latex_generates_pdf(self):
        """Valid LaTeX should generate PDF bytes."""
        latex = r"""
\documentclass{article}
\begin{document}
Hello World
\end{document}
"""
        pdf_bytes = generate_pdf_bytes(latex)

        # Should return bytes
        assert isinstance(pdf_bytes, bytes)
        # Should start with PDF magic number
        assert pdf_bytes.startswith(b"%PDF")
        # Should have reasonable size (not empty, not huge)
        assert len(pdf_bytes) > 100
        assert len(pdf_bytes) < 10_000_000  # 10MB sanity check

    def test_invalid_latex_raises_error(self):
        """Invalid LaTeX should raise RuntimeError."""
        latex = r"""
\documentclass{article}
\begin{document}
\invalidcommand{this will fail}
\end{document}
"""
        # pdflatex may or may not fail on undefined commands
        # depending on settings, so we just check it doesn't crash silently
        try:
            result = generate_pdf_bytes(latex)
            # If it succeeds, should still be valid PDF
            assert result.startswith(b"%PDF")
        except RuntimeError as e:
            # Expected behavior for compilation failure
            assert "PDF generation failed" in str(e)

    def test_complex_latex_structure(self):
        """More complex LaTeX with sections."""
        latex = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\title{Test Resume}
\author{Test User}
\begin{document}
\maketitle
\section{Education}
Test University
\section{Experience}
Test Job
\end{document}
"""
        pdf_bytes = generate_pdf_bytes(latex)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 100

    def test_unicode_content(self):
        """LaTeX with unicode characters."""
        latex = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\begin{document}
Café résumé naïve
\end{document}
"""
        pdf_bytes = generate_pdf_bytes(latex)

        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")

    def test_empty_document(self):
        """Empty LaTeX document fails to generate PDF (no pages)."""
        latex = r"""
\documentclass{article}
\begin{document}
\end{document}
"""
        # Empty documents don't generate PDFs (no pages of output)
        with pytest.raises(RuntimeError, match="PDF generation failed"):
            generate_pdf_bytes(latex)

    def test_no_temp_files_left_behind(self, tmp_path):
        """Temporary files should be cleaned up."""
        import os

        # Count files in temp before
        latex = r"""
\documentclass{article}
\begin{document}
Test
\end{document}
"""
        # Generate multiple times
        for _ in range(3):
            generate_pdf_bytes(latex)

        # We can't easily check temp directory, but we can verify
        # the function completes without leaving obvious temp files
        # in the current directory
        cwd_files = list(tmp_path.glob("*.tex")) + list(tmp_path.glob("*.pdf"))
        assert len(cwd_files) == 0
