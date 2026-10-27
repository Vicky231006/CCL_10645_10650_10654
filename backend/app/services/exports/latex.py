"""LaTeX export modelled on the structure of Jake's Resume (jakegut/resume, MIT licence).

The generated source is a clean, editable rendition of that template's structure.
Formatting follows the same practical, ATS-friendly single-column layout. The template
itself is third-party work (MIT) and is not claimed as original Resumo work.
"""
from __future__ import annotations

from app.schemas.resume import ResumeContent
from app.services.exports.links import ensure_url, link_label

_ESCAPES = {
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


def tex_escape(text: str) -> str:
    out = []
    for ch in text or "":
        out.append(_ESCAPES.get(ch, ch))
    return "".join(out)


def _url_escape(url: str) -> str:
    return (url or "").replace("\\", "").replace(" ", "")


PREAMBLE = r"""% ---------------------------------------------------------------------------
% Resumo export — structure inspired by Jake's Resume (github.com/jakegut/resume)
% Jake's Resume is licensed under the MIT License. This generated file is a
% faithful single-column rendition; Resumo does not claim ownership of that template.
% ---------------------------------------------------------------------------
\documentclass[letterpaper,11pt]{article}

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

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\pdfgentounicode=1

\newcommand{\resumeItem}[1]{
  \item\small{ {#1 \vspace{-2pt}}}
}
\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
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
"""


def render_latex(content: ResumeContent) -> str:
    c = content.contact
    lines = [PREAMBLE, r"\begin{document}", "", r"\begin{center}"]
    lines.append(r"    \textbf{\Huge \scshape " + tex_escape(c.name or "Your Name") + r"} \\ \vspace{1pt}")
    contact_bits = []
    if c.phone:
        contact_bits.append(r"\small " + tex_escape(c.phone))
    if c.email:
        contact_bits.append(r"\href{mailto:" + tex_escape(c.email) + r"}{\underline{" + tex_escape(c.email) + r"}}")
    for link in c.links:
        if link.url:
            curl = ensure_url(link.url)
            label = link.label or link_label(link.url)
            if curl:
                contact_bits.append(r"\href{" + _url_escape(curl) + r"}{\underline{" + tex_escape(label) + r"}}")
            else:
                contact_bits.append(r"\small " + tex_escape(label))
    if c.location:
        contact_bits.append(r"\small " + tex_escape(c.location))
    if contact_bits:
        lines.append("    " + r" $|$ ".join(contact_bits) + r" \\")
    lines.append(r"\end{center}")
    lines.append("")

    order = content.section_order or ["summary", "experience", "projects", "education", "skills",
                                      "certifications", "achievements"]
    visibility = content.section_visibility or {}

    def section(title: str):
        lines.append("")
        lines.append(r"\section{" + tex_escape(title) + "}")

    for sec in order:
        if visibility.get(sec) is False:
            continue
        if sec == "summary" and content.summary:
            section("Summary")
            lines.append(tex_escape(content.summary) + r" \\")
        elif sec == "experience" and content.experience:
            section("Experience")
            lines.append(r"  \resumeSubHeadingListStart")
            for exp in content.experience:
                dates = " -- ".join([d for d in [exp.start, exp.end] if d])
                lines.append(
                    r"    \resumeSubheading{" + tex_escape(exp.role or "") + "}{" + tex_escape(dates) + "}{"
                    + tex_escape(exp.company or "") + "}{" + tex_escape(exp.location or "") + "}"
                )
                if exp.bullets:
                    lines.append(r"      \resumeItemListStart")
                    for b in exp.bullets:
                        lines.append(r"        \resumeItem{" + tex_escape(b) + "}")
                    lines.append(r"      \resumeItemListEnd")
            lines.append(r"  \resumeSubHeadingListEnd")
        elif sec == "projects" and content.projects:
            section("Projects")
            lines.append(r"  \resumeSubHeadingListStart")
            for proj in content.projects:
                head = r"\textbf{" + tex_escape(proj.name) + "}"
                if proj.tech:
                    head += r" $|$ \emph{" + tex_escape(", ".join(proj.tech)) + "}"
                purl = ensure_url(proj.link) if proj.link else ""
                if purl:
                    link = r" \href{" + _url_escape(purl) + r"}{\underline{" + tex_escape(link_label(proj.link)) + r"}}"
                elif proj.link:
                    link = r" " + tex_escape(proj.link)
                else:
                    link = ""
                lines.append(r"    \resumeProjectHeading{" + head + "}{}" + link)
                if proj.bullets:
                    lines.append(r"      \resumeItemListStart")
                    for b in proj.bullets:
                        lines.append(r"        \resumeItem{" + tex_escape(b) + "}")
                    lines.append(r"      \resumeItemListEnd")
            lines.append(r"  \resumeSubHeadingListEnd")
        elif sec == "education" and content.education:
            section("Education")
            lines.append(r"  \resumeSubHeadingListStart")
            for ed in content.education:
                dates = " -- ".join([d for d in [ed.start, ed.end] if d])
                lines.append(
                    r"    \resumeSubheading{" + tex_escape(ed.institution or "") + "}{" + tex_escape(dates) + "}{"
                    + tex_escape(ed.degree or "") + "}{" + tex_escape(ed.location or "") + "}"
                )
                if ed.details:
                    lines.append(r"      \resumeItemListStart")
                    for d in ed.details:
                        lines.append(r"        \resumeItem{" + tex_escape(d) + "}")
                    lines.append(r"      \resumeItemListEnd")
            lines.append(r"  \resumeSubHeadingListEnd")
        elif sec == "skills" and content.skills:
            section("Technical Skills")
            lines.append(r" \begin{itemize}[leftmargin=0.15in, label={}]")
            for group in content.skills:
                if group.items:
                    lines.append(r"    \small{\item{\textbf{" + tex_escape(group.category) + "}{: "
                                 + tex_escape(", ".join(group.items)) + "}}}")
            lines.append(r" \end{itemize}")
        elif sec == "certifications" and content.certifications:
            section("Certifications")
            lines.append(r" \begin{itemize}[leftmargin=0.15in, label={}]")
            for item in content.certifications:
                lines.append(r"    \small{\item{" + tex_escape(item) + "}}")
            lines.append(r" \end{itemize}")
        elif sec == "achievements" and content.achievements:
            section("Achievements")
            lines.append(r" \begin{itemize}[leftmargin=0.15in, label={}]")
            for item in content.achievements:
                lines.append(r"    \small{\item{" + tex_escape(item) + "}}")
            lines.append(r" \end{itemize}")

    lines.append("")
    lines.append(r"\end{document}")
    return "\n".join(lines) + "\n"
