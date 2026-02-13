"""Generate PDF from LaTeX using pdflatex."""

import os
import subprocess
import tempfile
from pathlib import Path


def generate_pdf_bytes(latex_content: str) -> bytes:
    """
    Generate PDF from LaTeX content and return bytes (no file writes).

    Args:
        latex_content: The LaTeX source code

    Returns:
        PDF file as bytes
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = Path(temp_dir) / "resume.tex"

        # Write LaTeX content
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        # Run pdflatex twice for proper references
        for _ in range(2):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, str(tex_file)],
                capture_output=True,
                text=True
            )

        # Check if PDF was generated
        pdf_file = Path(temp_dir) / "resume.pdf"
        if not pdf_file.exists():
            raise RuntimeError(f"PDF generation failed. LaTeX output:\n{result.stdout}\n{result.stderr}")

        # Read PDF into memory
        with open(pdf_file, 'rb') as f:
            return f.read()


def generate_pdf(latex_content: str, output_filename: str, output_dir: str = "output") -> str:
    """
    Generate PDF from LaTeX content.

    Args:
        latex_content: The LaTeX source code
        output_filename: Base name for output (e.g., "resume+jake.pdf")
        output_dir: Directory to save output

    Returns:
        Path to the generated PDF file
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create a temporary directory for LaTeX compilation
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file = Path(temp_dir) / "resume.tex"

        # Write LaTeX content
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        # Run pdflatex twice for proper references
        for _ in range(2):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, str(tex_file)],
                capture_output=True,
                text=True
            )

        # Check if PDF was generated
        pdf_file = Path(temp_dir) / "resume.pdf"
        if not pdf_file.exists():
            raise RuntimeError(f"PDF generation failed. LaTeX output:\n{result.stdout}\n{result.stderr}")

        # Copy to output directory with desired name
        final_pdf = output_path / output_filename

        # If filename doesn't end with .pdf, add it
        if not final_pdf.suffix == '.pdf':
            final_pdf = final_pdf.with_suffix('.pdf')

        # Copy the file
        with open(pdf_file, 'rb') as src, open(final_pdf, 'wb') as dst:
            dst.write(src.read())

        return str(final_pdf)


def generate_latex_file(latex_content: str, output_filename: str, output_dir: str = "output") -> str:
    """
    Save LaTeX content to a .tex file.

    Args:
        latex_content: The LaTeX source code
        output_filename: Base name for output (e.g., "resume+jake.tex")
        output_dir: Directory to save output

    Returns:
        Path to the saved LaTeX file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    tex_file = output_path / output_filename

    # If filename doesn't end with .tex, add it
    if not tex_file.suffix == '.tex':
        tex_file = tex_file.with_suffix('.tex')

    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)

    return str(tex_file)
