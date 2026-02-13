"""Generate LaTeX from structured resume data."""

from .md_parser import Resume, ContactInfo, Education, Experience, Project, escape_latex


def generate_contact_latex(contact: ContactInfo) -> str:
    """Generate the contact/heading section."""
    name = escape_latex(contact.name) if contact.name else "Your Name"

    parts = []
    if contact.phone:
        parts.append(escape_latex(contact.phone))
    if contact.email:
        parts.append(f"\\href{{mailto:{contact.email}}}{{\\underline{{{escape_latex(contact.email)}}}}}")
    if contact.linkedin:
        # Extract just the username for display
        linkedin_display = contact.linkedin.replace('https://', '').replace('http://', '').replace('www.', '')
        parts.append(f"\\href{{{contact.linkedin}}}{{\\underline{{{escape_latex(linkedin_display)}}}}}")
    if contact.github:
        github_display = contact.github.replace('https://', '').replace('http://', '').replace('www.', '')
        parts.append(f"\\href{{{contact.github}}}{{\\underline{{{escape_latex(github_display)}}}}}")

    contact_line = " $|$ ".join(parts)

    return f"""%----------HEADING----------
\\begin{{center}}
    \\textbf{{\\Huge \\scshape {name}}} \\\\ \\vspace{{1pt}}
    \\small {contact_line}
\\end{{center}}
"""


def generate_education_latex(education: list[Education]) -> str:
    """Generate the education section."""
    if not education:
        return ""

    latex = "%-----------EDUCATION-----------\n\\section{Education}\n  \\resumeSubHeadingListStart\n"

    for edu in education:
        school = escape_latex(edu.school)
        location = escape_latex(edu.location)
        degree = escape_latex(edu.degree)
        date = escape_latex(edu.date)

        latex += f"""    \\resumeSubheading
      {{{school}}}{{{location}}}
      {{{degree}}}{{{date}}}
"""

        if edu.details:
            latex += "      \\resumeItemListStart\n"
            for detail in edu.details:
                latex += f"        \\resumeItem{{{escape_latex(detail)}}}\n"
            latex += "      \\resumeItemListEnd\n"

    latex += "  \\resumeSubHeadingListEnd\n"
    return latex


def generate_experience_latex(experiences: list[Experience]) -> str:
    """Generate the experience section."""
    if not experiences:
        return ""

    latex = "%-----------EXPERIENCE-----------\n\\section{Experience}\n  \\resumeSubHeadingListStart\n"

    for exp in experiences:
        company = escape_latex(exp.company)
        location = escape_latex(exp.location)
        role = escape_latex(exp.role)
        date = escape_latex(exp.date)

        latex += f"""    \\resumeSubheading
      {{{role}}}{{{date}}}
      {{{company}}}{{{location}}}
"""

        if exp.bullets:
            latex += "      \\resumeItemListStart\n"
            for bullet in exp.bullets:
                # Already cleaned markdown, just escape latex
                latex += f"        \\resumeItem{{{escape_latex(bullet)}}}\n"
            latex += "      \\resumeItemListEnd\n"

    latex += "  \\resumeSubHeadingListEnd\n"
    return latex


def generate_projects_latex(projects: list[Project]) -> str:
    """Generate the projects section."""
    if not projects:
        return ""

    latex = "%-----------PROJECTS-----------\n\\section{Projects}\n    \\resumeSubHeadingListStart\n"

    for proj in projects:
        name = escape_latex(proj.name)
        if proj.link:
            # Format: \textbf{Name} $|$ \emph{Tech}
            link = escape_latex(proj.link)
            heading = f"\\href{{{proj.link}}}{{\\textbf{{{name}}}}}"
        else:
            heading = f"\\textbf{{{name}}}"

        # Date/period for project
        date = ""

        latex += f"""      \\resumeProjectHeading
          {{{heading} $|$ \\emph{{Project}}}}{{{date}}}
"""

        if proj.bullets:
            latex += "          \\resumeItemListStart\n"
            for bullet in proj.bullets:
                latex += f"            \\resumeItem{{{escape_latex(bullet)}}}\n"
            latex += "          \\resumeItemListEnd\n"

    latex += "    \\resumeSubHeadingListEnd\n"
    return latex


def generate_skills_latex(skills: str, interests: str) -> str:
    """Generate the skills section."""
    if not skills:
        return ""

    latex = "%-----------PROGRAMMING SKILLS-----------\n\\section{Technical Skills}\n \\begin{itemize}[leftmargin=0.15in, label={}]\n    \\small{\\item{\n"

    # Parse skills - they might be in format: Category: items | Category: items
    # Or just a list
    skill_items = []

    # Split by | to get categories
    categories = [s.strip() for s in skills.split('|')]

    for cat in categories:
        if ':' in cat:
            # Format: "Languages: Python, C++"
            cat_clean = escape_latex(cat)
            skill_items.append(f"     \\textbf{{{cat_clean}}}")
        else:
            # Just a list, make it Languages
            cat_clean = escape_latex(cat)
            skill_items.append(f"     \\textbf{{{cat_clean}}}")

    latex += " \\\\\n".join(skill_items)
    latex += "\n    }}\n \\end{itemize}\n"

    return latex


def generate_full_latex(resume: Resume) -> str:
    """Generate complete LaTeX document."""

    # Read the template preamble
    template_preamble = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\input{glyphtounicode}


%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
\usepackage{charter}


\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure that generate pdf is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%


\begin{document}
"""

    # Build content sections
    content = ""
    content += generate_contact_latex(resume.contact)
    content += "\n"
    content += generate_education_latex(resume.education)
    content += "\n"
    content += generate_experience_latex(resume.experience)
    content += "\n"
    content += generate_projects_latex(resume.projects)
    content += "\n"
    content += generate_skills_latex(resume.skills, resume.interests)

    # Close document
    footer = r"""
%-------------------------------------------
\end{document}
"""

    return template_preamble + content + footer
