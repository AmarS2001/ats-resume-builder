"""ATS Resume Builder — MCP Server.

Exposes four tools to any AI IDE via the Model Context Protocol:
  1. get_profile   — returns the candidate's profile.yaml as JSON
  2. get_template  — returns the HTML resume template
  3. get_prompt    — returns the ATS system prompt for resume generation
  4. generate_pdf  — converts LLM-generated resume HTML → A4 PDF
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from fastmcp import FastMCP

from .gdrive import upload_file_to_drive
from .pdf import html_to_pdf
from .profile import load_profile
from .renderer import get_template, render_resume

# ---------------------------------------------------------------------------
# Resolve project root + configurable output directory
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Users can set ATS_OUTPUT_DIR env-var to control where PDFs/HTML land.
# Defaults to <project_root>/output
_OUTPUT_DIR = Path(os.environ.get("ATS_OUTPUT_DIR", str(_PROJECT_ROOT / "output")))

# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "ats-resume-builder",
    instructions=(
        "ATS Resume Builder tools. Before constructing the resume HTML or calling generate_pdf(), "
        "you MUST call get_prompt() to read the strict ATS formatting rules, and call get_template() "
        "to read the design system structure. Failing to fetch get_prompt() first will result in formatting "
        "rejection. Once you have gathered inputs using get_profile(), get_prompt(), and get_template(), "
        "craft the resume HTML yourself and call generate_pdf() to render the final output."
    ),
)


# ── Tool 1: get_profile ──────────────────────────────────────────────────────


@mcp.tool()
def get_profile() -> dict:
    """Return the candidate's full profile data from profile.yaml.

    The returned JSON mirrors the YAML structure.

    Use this data together with the job description to tailor the resume.
    """
    return load_profile()



# ── Tool 2: get_template ─────────────────────────────────────────────────────


@mcp.tool()
def get_resume_template() -> str:
    """Return the raw HTML of the resume template (template.html).

    The template defines the CSS design system and the HTML structure
    that the generated resume MUST follow.  Preserve all class names,
    CSS variables, and semantic tags exactly.
    """
    return get_template()


# ── Tool 3: get_prompt ────────────────────────────────────────────────────────


@mcp.tool()
def get_prompt() -> str:
    """Return the ATS resume-builder system prompt (prompt.md).

    This prompt contains the rules, keyword-optimisation strategy, and
    section-by-section writing guidelines the LLM should follow when
    generating the resume HTML.
    """
    import importlib.resources
    try:
        ref = importlib.resources.files("ats_mcp") / "prompt.md"
        if ref.is_file():
            return ref.read_text(encoding="utf-8")
    except Exception:
        pass
    prompt_path = _PROJECT_ROOT / "prompt.md"
    return prompt_path.read_text(encoding="utf-8")



# ── Tool 4: generate_pdf ─────────────────────────────────────────────────────


def _slugify(text: str) -> str:
    """Turn a string into a filename-safe slug."""
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s]+", "_", text).strip("_")


@mcp.tool()
def generate_pdf(resume_html: str, company_name: str) -> str:
    """Convert the finished resume HTML into an A4 PDF.

    Parameters
    ----------
    resume_html:
        The complete, self-contained HTML string for the resume.
        If it already includes a ``<style>`` block it will be used as-is;
        otherwise the template CSS is injected automatically.
    company_name:
        Used for the output filename: ``<CandidateName>_<CompanyName>.pdf``

    Returns
    -------
    str
        The absolute path of the generated PDF file.

    Environment
    -----------
    ATS_OUTPUT_DIR
        Controls the directory where PDFs and intermediate HTML files are
        written.  Defaults to ``<project_root>/output``.
    """
    # Determine if the HTML already carries its own <style> block.
    if "<style" not in resume_html.lower():
        resume_html = render_resume(resume_html)

    # Build the output filename from the candidate name in profile.yaml.
    profile = load_profile()
    
    candidate_name = ""
    if isinstance(profile, dict):
        if "personal" in profile and isinstance(profile["personal"], dict):
            candidate_name = profile["personal"].get("name")
        elif "candidate" in profile and isinstance(profile["candidate"], dict):
            candidate_name = profile["candidate"].get("name")
            
    if not candidate_name:
        candidate_name = "Resume"
        
    name_slug = _slugify(candidate_name)
    company_slug = _slugify(company_name)

    # Also save the intermediate HTML for debugging / manual review.
    html_path = _OUTPUT_DIR / f"{name_slug}_{company_slug}.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(resume_html, encoding="utf-8")

    pdf_path = _OUTPUT_DIR / f"{name_slug}_{company_slug}.pdf"
    result = html_to_pdf(resume_html, pdf_path)

    return str(result)


# ── Tool 5: upload_to_gdrive ──────────────────────────────────────────────────


@mcp.tool()
def upload_to_gdrive(file_path: str, folder_id: str | None = None) -> str:
    """Upload a generated PDF resume (or any other file) to Google Drive.

    Parameters
    ----------
    file_path : str
        The absolute path to the PDF file to upload.
    folder_id : str | None, optional
        Target folder ID in Google Drive. If omitted, the GDRIVE_FOLDER_ID
        environment variable is used. If that is also omitted, uploads to the root.

    Returns
    -------
    str
        A string summarizing the upload result including the file name, ID, and link.

    Environment Variables
    ---------------------
    At least one Google Drive credentials setup is required:
    - GDRIVE_SERVICE_ACCOUNT_JSON: The raw JSON string of a service account key.
    - GDRIVE_SERVICE_ACCOUNT_FILE: Path to a service account JSON file.
    - GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN: OAuth 2.0 Credentials.
    - GDRIVE_FOLDER_ID: Optional default folder ID to upload files to.
    """
    result = upload_file_to_drive(file_path, folder_id)
    return (
        f"File '{result['name']}' uploaded successfully to Google Drive.\n"
        f"File ID: {result['id']}\n"
        f"Web View Link: {result.get('webViewLink', 'N/A')}"
    )


# ── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point registered in pyproject.toml ``[project.scripts]``."""
    mcp.run()


if __name__ == "__main__":
    main()
