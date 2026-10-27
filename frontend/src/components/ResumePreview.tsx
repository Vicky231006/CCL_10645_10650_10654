import type { ResumeContent } from "../lib/types";
import { cn, ensureUrl, linkLabel } from "../lib/utils";

/** A faithful, print-like preview of the structured resume (Jake's-template inspired). */
export function ResumePreview({ content, pageSize = "A4" }: { content: ResumeContent; pageSize?: string }) {
  const order = content.section_order?.length
    ? content.section_order
    : ["summary", "experience", "projects", "education", "skills", "certifications", "achievements"];
  const vis = content.section_visibility ?? {};
  const dims = pageSize === "LETTER" ? "aspect-[8.5/11]" : "aspect-[210/297]";
  const c = content.contact;

  function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
      <section className="mb-3">
        <h3 className="border-b border-ink pb-0.5 text-[11px] font-bold uppercase tracking-wide text-ink">{title}</h3>
        <div className="mt-1.5 space-y-1.5 text-[10.5px] leading-snug text-ink-soft">{children}</div>
      </section>
    );
  }

  const contactBits: { text: string; url?: string }[] = [
    c.email ? { text: c.email, url: `mailto:${c.email}` } : null,
    c.phone ? { text: c.phone } : null,
    c.location ? { text: c.location } : null,
    ...c.links.filter((l) => l.url).map((l) => ({ text: l.label || linkLabel(l.url), url: ensureUrl(l.url) })),
  ].filter(Boolean) as { text: string; url?: string }[];

  return (
    <div className={cn("w-full bg-white shadow-soft", dims)} data-testid="resume-preview">
      <div className="h-full w-full overflow-hidden p-[7%] text-ink">
        <header className="mb-3 text-center">
          <p className="font-serif text-[20px] font-bold leading-tight">{c.name || "Your Name"}</p>
          {c.headline && <p className="text-[10.5px] text-ink-muted">{c.headline}</p>}
          {contactBits.length > 0 && (
            <p className="mt-0.5 text-[9.5px] text-ink-muted">
              {contactBits.map((b, i) => (
                <span key={i}>
                  {i > 0 && "  •  "}
                  {b.url ? (
                    <a
                      href={b.url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="text-forest underline decoration-dotted underline-offset-2"
                    >
                      {b.text}
                    </a>
                  ) : (
                    b.text
                  )}
                </span>
              ))}
            </p>
          )}
        </header>

        {order.map((key) => {
          if (vis[key] === false) return null;
          if (key === "summary" && content.summary) {
            return (
              <Section key={key} title="Summary">
                <p>{content.summary}</p>
              </Section>
            );
          }
          if (key === "experience" && content.experience.length) {
            return (
              <Section key={key} title="Experience">
                {content.experience.map((e, i) => (
                  <div key={i}>
                    <div className="flex justify-between font-semibold text-ink">
                      <span>
                        {e.role}
                        {e.company && ` — ${e.company}`}
                      </span>
                      <span className="font-normal text-ink-muted">{[e.start, e.end].filter(Boolean).join(" – ")}</span>
                    </div>
                    {e.location && <p className="italic text-ink-muted">{e.location}</p>}
                    <ul className="ml-3 list-disc">
                      {e.bullets.filter(Boolean).map((b, j) => (
                        <li key={j}>{b}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </Section>
            );
          }
          if (key === "projects" && content.projects.length) {
            return (
              <Section key={key} title="Projects">
                {content.projects.map((p, i) => (
                  <div key={i}>
                    <div className="flex justify-between font-semibold text-ink">
                      <span>
                        {p.name}
                        {p.tech.length > 0 && <span className="font-normal text-ink-muted"> | {p.tech.join(", ")}</span>}
                      </span>
                      {p.link &&
                        (ensureUrl(p.link) ? (
                          <a
                            href={ensureUrl(p.link)}
                            target="_blank"
                            rel="noreferrer noopener"
                            className="font-normal text-forest underline decoration-dotted underline-offset-2"
                          >
                            {linkLabel(p.link)}
                          </a>
                        ) : (
                          <span className="font-normal text-ink-muted">{p.link}</span>
                        ))}
                    </div>
                    <ul className="ml-3 list-disc">
                      {p.bullets.filter(Boolean).map((b, j) => (
                        <li key={j}>{b}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </Section>
            );
          }
          if (key === "education" && content.education.length) {
            return (
              <Section key={key} title="Education">
                {content.education.map((e, i) => (
                  <div key={i}>
                    <div className="flex justify-between font-semibold text-ink">
                      <span>
                        {e.institution}
                        {e.degree && ` — ${e.degree}`}
                      </span>
                      <span className="font-normal text-ink-muted">{[e.start, e.end].filter(Boolean).join(" – ")}</span>
                    </div>
                    {e.details.filter(Boolean).length > 0 && (
                      <ul className="ml-3 list-disc">
                        {e.details.filter(Boolean).map((d, j) => (
                          <li key={j}>{d}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </Section>
            );
          }
          if (key === "skills" && content.skills.length) {
            return (
              <Section key={key} title="Skills">
                {content.skills.map((s, i) => (
                  <p key={i}>
                    {s.category && s.category !== "Skills" && <span className="font-semibold text-ink">{s.category}: </span>}
                    {s.items.join(", ")}
                  </p>
                ))}
              </Section>
            );
          }
          if (key === "certifications" && content.certifications.length) {
            return (
              <Section key={key} title="Certifications">
                <ul className="ml-3 list-disc">
                  {content.certifications.filter(Boolean).map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </Section>
            );
          }
          if (key === "achievements" && content.achievements.length) {
            return (
              <Section key={key} title="Achievements">
                <ul className="ml-3 list-disc">
                  {content.achievements.filter(Boolean).map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </Section>
            );
          }
          return null;
        })}
      </div>
    </div>
  );
}
