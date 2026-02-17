"""Parse markdown resume into structured data."""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ContactInfo:
    name: str = ""
    location: str = ""
    phone: str = ""
    email: str = ""
    linkedin: str = ""
    github: str = ""


@dataclass
class Education:
    school: str = ""
    location: str = ""
    degree: str = ""
    date: str = ""
    details: List[str] = field(default_factory=list)


@dataclass
class Experience:
    company: str = ""
    location: str = ""
    role: str = ""
    date: str = ""
    bullets: List[str] = field(default_factory=list)


@dataclass
class Project:
    name: str = ""
    link: str = ""
    tech: str = ""
    bullets: List[str] = field(default_factory=list)


@dataclass
class Resume:
    contact: ContactInfo = field(default_factory=ContactInfo)
    education: List[Education] = field(default_factory=list)
    experience: List[Experience] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    skills: str = ""
    interests: str = ""


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters (but not backslashes - those are for commands)."""
    # Use placeholders for already-escaped sequences to protect them
    placeholders = {}
    counter = 0

    # Protect already-escaped sequences (preceded by backslash)
    for char in ['&', '%', '$', '#', '_', '{', '}', '~', '^']:
        pattern = f'\\{char}'
        while pattern in text:
            placeholder = f"\x00ESC{counter}\x00"
            placeholders[placeholder] = pattern
            text = text.replace(pattern, placeholder, 1)
            counter += 1

    # Now escape special characters
    text = text.replace("{", "\\{")
    text = text.replace("}", "\\}")
    text = text.replace("&", "\\&")
    text = text.replace("%", "\\%")
    text = text.replace("$", "\\$")
    text = text.replace("#", "\\#")
    text = text.replace("_", "\\_")
    text = text.replace("~", "\\textasciitilde{}")
    text = text.replace("^", "\\textasciicircum{}")

    # Restore protected sequences
    for placeholder, original in placeholders.items():
        text = text.replace(placeholder, original)

    return text


def clean_markdown(text: str) -> str:
    """Remove markdown bold/italic markers for LaTeX processing."""
    text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'\\textbf{\\textit{\1}}', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', text)
    text = re.sub(r'\*([^*]+)\*', r'\\textit{\1}', text)
    return text


def parse_contact_line(line: str) -> ContactInfo:
    """Parse the header contact line."""
    contact = ContactInfo()

    # Extract name (first line should be # Name or **Name**)
    name_match = re.match(r'^#\s*\*\*([^*]+)\*\*', line)
    if name_match:
        contact.name = name_match.group(1).strip()

    return contact


def parse_contact_details(lines: List[str]) -> ContactInfo:
    """Parse contact details from the line after name."""
    contact = ContactInfo()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract name if present
        if line.startswith('# **'):
            match = re.match(r'^#\s*\*\*([^*]+)\*\*', line)
            if match:
                contact.name = match.group(1).strip()
            continue

        # Parse contact line with | separators
        # Format: Location | LinkedIn | Phone | Email | GitHub
        parts = [p.strip() for p in line.split('|')]

        for part in parts:
            # LinkedIn
            if 'linkedin.com' in part.lower():
                match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', part)
                if match:
                    contact.linkedin = match.group(2)
            # GitHub
            elif 'github.com' in part.lower():
                match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', part)
                if match:
                    contact.github = match.group(2)
            # Email
            elif 'mailto:' in part:
                match = re.search(r'\[([^\]]+)\]\(mailto:([^)]+)\)', part)
                if match:
                    contact.email = match.group(2)
            # Phone (has + and numbers, or \+ for escaped plus)
            elif re.search(r'\\?\+[\d\s-]+', part):
                phone_match = re.search(r'(\\?\+[\d\s-]+)', part)
                if phone_match:
                    contact.phone = phone_match.group(1).replace(' ', '').replace('-', '').replace('\\', '')
            # Location (first part usually)
            elif not contact.location and ',' in part and 'http' not in part:
                contact.location = part

    return contact


def parse_education_section(lines: List[str]) -> List[Education]:
    """Parse education section."""
    educations = []
    current = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for school line (usually **School** **Location** or tab-separated)
        # Handle: **School**	**Location** (tab separated)
        school_match = re.match(r'\*\*([^*]+?)\*\*\s+\*\*([^*]+)\*\*', line)
        # Handle: **School**	Location without closing ** before tab
        if not school_match:
            school_match = re.match(r'\*\*([^*]+?)\*\*\s+([^|]+)', line)
        if school_match and any(kw in line.lower() for kw in ['university', 'institute', 'college', 'vit', 'iit', 'bits']):
            # Make sure this looks like an education entry
            school_name = school_match.group(1).strip()
            if any(kw in school_name.lower() for kw in ['university', 'institute', 'college', 'vit', 'iit', 'bits']):
                if current:
                    educations.append(current)
                current = Education(
                    school=school_match.group(1).strip(),
                    location=school_match.group(2).strip()
                )
                continue

        # Degree and date line (format: *Degree* Date or *Degree*\tDate or just *Degree*)
        if current and line.startswith('*') and not line.startswith('* '):
            # Check for *Degree*\tDate pattern (tab-separated)
            tab_match = re.match(r'\*([^*]+?)\*?\t+(.+)', line)
            if tab_match:
                current.degree = tab_match.group(1).strip()
                current.date = tab_match.group(2).strip()
            else:
                # Check for *Degree* Date pattern (space-separated)
                degree_match = re.match(r'\*([^*]+)\*\s+(.+)', line)
                if degree_match:
                    current.degree = degree_match.group(1).strip()
                    current.date = degree_match.group(2).strip()
                else:
                    # Just *Degree* without date
                    degree_only = re.match(r'\*([^*]+)\*', line)
                    if degree_only:
                        current.degree = degree_only.group(1).strip()
            continue

        # GPA and awards as bullet points
        if current and line.startswith('*'):
            # Remove the bullet marker (* or * ) but not formatting asterisks
            detail = re.sub(r'^\*\s*', '', line).strip()
            if detail:
                current.details.append(detail)

    if current:
        educations.append(current)

    return educations


def parse_experience_section(lines: List[str]) -> List[Experience]:
    """Parse work experience section."""
    experiences = []
    current = None
    in_bullets = False

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Company and location: **Company** **Location** or **Company\tLocation**
        company_match = re.match(r'\*\*([^*]+?)\*\*\s+\*\*([^*]+)\*\*', line_stripped)
        # Handle tab-separated in one block: **Company\tLocation**
        if not company_match:
            tab_match = re.match(r'\*\*([^\*]+?)\t+([^\*]+)\*\*', line_stripped)
            if tab_match:
                company_match = tab_match
        if company_match and not line_stripped.startswith('* '):
            if current and (current.bullets or current.company):
                experiences.append(current)
            current = Experience(
                company=company_match.group(1).strip(),
                location=company_match.group(2).strip()
            )
            in_bullets = False
            continue

        # Role and date: *Role Date* or *Role\tDate*
        if current and not current.role and '*''' in line_stripped:
            role_match = re.match(r'\*([^*]+)\*', line_stripped)
            if role_match:
                full = role_match.group(1).strip()
                # Split on tab or look for date patterns
                parts = re.split(r'\t+|\s{2,}', full)
                if len(parts) >= 2:
                    current.role = parts[0].strip()
                    current.date = parts[1].strip()
                else:
                    # Try to find date pattern
                    date_match = re.search(r'((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[\w\s-]*\d{4}[\s\w-]*)', full, re.IGNORECASE)
                    if date_match:
                        current.date = date_match.group(1).strip()
                        current.role = full[:date_match.start()].strip()
                    else:
                        current.role = full
            continue

        # Bullet points
        if line_stripped.startswith('*') and current:
            # Remove the bullet marker (* or * ) but not formatting asterisks
            bullet = re.sub(r'^\*\s*', '', line_stripped).strip()
            if bullet:
                current.bullets.append(bullet)

    if current and (current.bullets or current.company):
        experiences.append(current)

    return experiences


def parse_project_section(lines: List[str]) -> List[Project]:
    """Parse projects section."""
    projects = []
    current = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Project name with link: **Name [link]**
        # Pattern: **Project Name [[link](url)]**
        project_match = re.match(r'\*\*([^[]+)\[\[([^\]]+)\]\(([^)]+)\)\]\*\*', line_stripped)
        if project_match:
            if current and current.bullets:
                projects.append(current)
            current = Project(
                name=project_match.group(1).strip(),
                link=project_match.group(3).strip()
            )
            continue

        # Alternative format without explicit link text
        alt_match = re.match(r'\*\*([^[]+)\[\s*\[([^\]]+)\]\(([^)]+)\)\s*\]\*\*', line_stripped)
        if alt_match:
            if current and current.bullets:
                projects.append(current)
            current = Project(
                name=alt_match.group(1).strip(),
                link=alt_match.group(3).strip()
            )
            continue

        # Simple format: **Project Name** then link on next line or inline
        simple_match = re.match(r'\*\*([^*]+)\*\*', line_stripped)
        if simple_match and 'Project' in line_stripped or line_stripped.startswith('**'):
            # Check if this looks like a project header
            if not line_stripped.startswith('* ') and '[' in line_stripped:
                if current and current.bullets:
                    projects.append(current)
                name = simple_match.group(1).strip()
                # Extract link if present
                link_match = re.search(r'\[([^\]]*)\]\(([^)]+)\)', line_stripped)
                if link_match:
                    current = Project(
                        name=name.replace(f'[{link_match.group(1)}]', '').strip(),
                        link=link_match.group(2)
                    )
                else:
                    current = Project(name=name)
                continue

        # Bullet points for project
        if line_stripped.startswith('*') and current:
            # Remove the bullet marker (* or * ) but not formatting asterisks
            bullet = re.sub(r'^\*\s*', '', line_stripped).strip()
            if bullet:
                current.bullets.append(bullet)

    if current and current.bullets:
        projects.append(current)

    return projects


def parse_skills_section(lines: List[str]) -> Tuple[str, str]:
    """Parse skills and interests section."""
    skills = ""
    interests = ""

    for line in lines:
        line = line.strip()
        if line.startswith('**Skills:**'):
            skills = line.replace('**Skills:**', '').strip()
        elif line.startswith('**Interests:**'):
            interests = line.replace('**Interests:**', '').strip()

    return skills, interests


def parse_markdown(content: str) -> Resume:
    """Main entry point: parse markdown resume content."""
    lines = content.split('\n')
    resume = Resume()

    # Find sections
    sections = {}
    current_section = None
    section_lines = []

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # Check for section headers (all caps like EDUCATION, EXPERIENCE or **EDUCATION**)
        # Remove ** markers for checking
        line_clean = line_stripped.replace('**', '')
        if line_clean.isupper() and len(line_clean) > 3:
            if current_section:
                sections[current_section] = section_lines
            current_section = line_stripped
            section_lines = []
        elif current_section:
            section_lines.append(line)
        else:
            # Header lines (before first section)
            if 'header' not in sections:
                sections['header'] = []
            sections['header'].append(line)

    if current_section:
        sections[current_section] = section_lines

    # Parse header
    if 'header' in sections:
        header_content = '\n'.join(sections['header'])
        resume.contact = parse_contact_details(sections['header'])

    # Parse sections
    for section_name, section_lines in sections.items():
        if 'EDUCATION' in section_name:
            resume.education = parse_education_section(section_lines)
        elif 'EXPERIENCE' in section_name or 'WORK' in section_name:
            resume.experience = parse_experience_section(section_lines)
        elif 'PROJECT' in section_name:
            resume.projects = parse_project_section(section_lines)
        elif 'SKILL' in section_name or 'INTEREST' in section_name:
            resume.skills, resume.interests = parse_skills_section(section_lines)

    return resume
