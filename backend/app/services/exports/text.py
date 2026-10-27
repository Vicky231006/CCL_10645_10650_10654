"""Plain-text (ATS-safe) export."""
from __future__ import annotations

from app.schemas.resume import ResumeContent


def render_text(content: ResumeContent) -> str:
    c = content.contact
    lines: list[str] = []
    if c.name:
        lines.append(c.name)
    if c.headline:
        lines.append(c.headline)
    contact_line = " | ".join([x for x in [c.email, c.phone, c.location] if x])
    if contact_line:
        lines.append(contact_line)
    for link in c.links:
        if link.url:
            lines.append(f"{link.label or 'Link'}: {link.url}")
    lines.append("")

    order = content.section_order or ["summary", "experience", "projects", "education", "skills",
                                      "certifications", "achievements"]
    visibility = content.section_visibility or {}

    def section(title: str):
        lines.append(title.upper())
        lines.append("-" * len(title))

    for sec in order:
        if visibility.get(sec) is False:
            continue
        if sec == "summary" and content.summary:
            section("Summary")
            lines.append(content.summary)
            lines.append("")
        elif sec == "experience" and content.experience:
            section("Experience")
            for exp in content.experience:
                header = (exp.role or "") + (f" — {exp.company}" if exp.company else "")
                dates = " – ".join([d for d in [exp.start, exp.end] if d])
                lines.append(f"{header}" + (f" ({dates})" if dates else ""))
                for b in exp.bullets:
                    lines.append(f"  - {b}")
                lines.append("")
        elif sec == "projects" and content.projects:
            section("Projects")
            for proj in content.projects:
                head = proj.name + (f" ({', '.join(proj.tech)})" if proj.tech else "")
                lines.append(head)
                for b in proj.bullets:
                    lines.append(f"  - {b}")
                if proj.link:
                    lines.append(f"  Link: {proj.link}")
                lines.append("")
        elif sec == "education" and content.education:
            section("Education")
            for ed in content.education:
                header = ed.institution + (f" — {ed.degree}" if ed.degree else "")
                dates = " – ".join([d for d in [ed.start, ed.end] if d])
                lines.append(header + (f" ({dates})" if dates else ""))
                for d in ed.details:
                    lines.append(f"  - {d}")
                lines.append("")
        elif sec == "skills" and content.skills:
            section("Skills")
            for group in content.skills:
                if group.items:
                    label = f"{group.category}: " if group.category and group.category != "Skills" else ""
                    lines.append(f"{label}{', '.join(group.items)}")
            lines.append("")
        elif sec == "certifications" and content.certifications:
            section("Certifications")
            for item in content.certifications:
                lines.append(f"  - {item}")
            lines.append("")
        elif sec == "achievements" and content.achievements:
            section("Achievements")
            for item in content.achievements:
                lines.append(f"  - {item}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
