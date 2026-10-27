import { Card } from "../../components/ui";

const groups = [
  {
    title: "Diagnose",
    items: [
      "Multi-format upload: PDF, DOCX, DOC, TXT, Markdown, RTF, ODT, LaTeX, HTML, and scanned images",
      "Structured, editable resume model you can correct",
      "Deterministic quality score across six weighted categories",
      "Exact excerpts, explanations and proposed corrections",
    ],
  },
  {
    title: "Match",
    items: [
      "Paste or save job descriptions; parse required vs preferred skills",
      "Keyword table with evidence location and status (found / weak / missing)",
      "Transparent alignment score with normalised synonyms",
      "Multiple resume versions compared against the same role",
    ],
  },
  {
    title: "Build",
    items: [
      "Jake's-template-inspired editor with live A4 / US Letter preview",
      "Truth-preserving AI rewriting: review, approve, apply",
      "Export PDF, DOCX, LaTeX and plain text from one source",
      "Portfolio pages, READMEs, bios, cover letters and outreach drafts",
    ],
  },
  {
    title: "Grow",
    items: [
      "Career gap reports tied to each job requirement",
      "Achievable project briefs with milestones and acceptance criteria",
      "Curated learning resources with valid links",
      "Application tracker connected to matches, resumes and roadmaps",
    ],
  },
];

export function Features() {
  return (
    <div className="container-page py-14">
      <p className="eyebrow">Capabilities</p>
      <h1 className="mt-2 font-serif text-4xl">Everything in one honest workspace</h1>
      <p className="mt-3 max-w-prose text-ink-muted">
        Resumo brings diagnosis, matching, building and planning together — with provenance on every claim.
      </p>
      <div className="mt-10 grid gap-5 sm:grid-cols-2">
        {groups.map((g) => (
          <Card key={g.title}>
            <h2 className="font-serif text-xl">{g.title}</h2>
            <ul className="mt-3 space-y-2 text-sm text-ink-soft">
              {g.items.map((i) => (
                <li key={i} className="flex gap-2">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-forest" aria-hidden />
                  {i}
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </div>
  );
}
