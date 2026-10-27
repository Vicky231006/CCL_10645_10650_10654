import { Card } from "../../components/ui";

const steps = [
  ["1. Create your profile", "Tell Resumo your degree, target roles, skills and projects — or skip and add it later. Incomplete profiles are fine."],
  ["2. Add a resume", "Upload any supported format or start from the editor. Resumo extracts a structured model and records a parsing confidence."],
  ["3. Correct and analyse", "Fix any extraction errors, then run a quality analysis. You'll get category scores, excerpts and specific fixes."],
  ["4. Match to a job", "Paste a job description. Resumo extracts requirements and shows which are evidenced, weak, or genuinely missing."],
  ["5. Close the gaps", "Generate a roadmap and project briefs. Each recommendation cites the job requirement behind it."],
  ["6. Build evidence", "Track milestones, publish honest portfolio assets, and export job-specific resume versions."],
];

export function HowItWorks() {
  return (
    <div className="container-page py-14">
      <p className="eyebrow">How it works</p>
      <h1 className="mt-2 font-serif text-4xl">A loop you can actually finish</h1>
      <p className="mt-3 max-w-prose text-ink-muted">
        Resumo is built as a cycle: diagnose, match, build, review. Every step produces something concrete you can use.
      </p>
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map(([title, body]) => (
          <Card key={title}>
            <h2 className="font-medium text-ink">{title}</h2>
            <p className="mt-1 text-sm text-ink-muted">{body}</p>
          </Card>
        ))}
      </div>
      <Card className="mt-8 bg-forest-tint">
        <h2 className="font-serif text-xl">What Resumo will never do</h2>
        <ul className="mt-3 grid gap-2 text-sm text-ink-soft sm:grid-cols-2">
          {[
            "Invent experience, metrics, employers or credentials",
            "Guarantee an ATS pass or an interview",
            "Present demo listings as live vacancies",
            "Scrape private profiles or bypass protections",
            "Add hidden pricing or premium gates",
            "Use your documents to train models without consent",
          ].map((t) => (
            <li key={t} className="flex gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-clay" aria-hidden />
              {t}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
