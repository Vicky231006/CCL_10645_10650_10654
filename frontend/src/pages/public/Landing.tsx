import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, CircleAlert, FileText, Search, Sparkles, Target } from "lucide-react";
import { Button, Card } from "../../components/ui";
import { Badge } from "../../components/ui";

const DEMO_RESUME = `Asha Rao — Backend-focused CS student
Built a REST API in Python; wrote unit tests; used PostgreSQL. Deployed with Docker.
Skills: Python, SQL, Docker, REST, Git`;

const DEMO_JD = `Backend Engineering Intern
Required: Python, REST API design, SQL, Docker, unit testing.
Preferred: FastAPI, cloud (AWS).`;

const DEMO_KEYWORDS: { term: string; importance: "required" | "preferred" }[] = [
  { term: "python", importance: "required" },
  { term: "rest", importance: "required" },
  { term: "sql", importance: "required" },
  { term: "docker", importance: "required" },
  { term: "unit testing", importance: "required" },
  { term: "fastapi", importance: "preferred" },
  { term: "aws", importance: "preferred" },
];

function DemoAnalysis() {
  const [jd, setJd] = useState(DEMO_JD);
  const results = useMemo(() => {
    return DEMO_KEYWORDS.map((k) => ({
      ...k,
      found: DEMO_RESUME.toLowerCase().includes(k.term.split(" ")[0]),
      inJd: jd.toLowerCase().includes(k.term.split(" ")[0]),
    })).filter((k) => k.inJd);
  }, [jd]);

  return (
    <Card className="shadow-raised">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <p className="eyebrow">Interactive demo</p>
          <h3 className="font-serif text-lg">See a match in your browser</h3>
        </div>
        <Badge tone="info">Sample data only</Badge>
      </div>
      <p className="mb-4 text-sm text-ink-muted">
        This demo runs entirely in your browser on labelled sample data. It shows how Resumo attributes each
        keyword to evidence or a gap — real analyses run on the server with your own documents.
      </p>
      <label htmlFor="demo-jd" className="text-sm font-medium text-ink-soft">
        Paste a job description to test
      </label>
      <textarea
        id="demo-jd"
        value={jd}
        onChange={(e) => setJd(e.target.value)}
        rows={4}
        className="mt-1 w-full rounded-md border border-stone-300 bg-ivory-50 p-3 text-sm focus:border-forest focus:outline-none"
      />
      <ul className="mt-4 space-y-2" aria-live="polite">
        {results.map((k) => (
          <li key={k.term} className="flex items-center justify-between rounded-md border border-stone-200 px-3 py-2 text-sm">
            <span className="inline-flex items-center gap-2 capitalize text-ink-soft">
              {k.found ? <Check className="h-4 w-4 text-forest" aria-hidden /> : <CircleAlert className="h-4 w-4 text-clay" aria-hidden />}
              {k.term}
            </span>
            <span className="flex items-center gap-2">
              <Badge tone={k.importance === "required" ? "critical" : "neutral"}>{k.importance}</Badge>
              <Badge tone={k.found ? "positive" : "warning"}>{k.found ? "evidenced" : "not evidenced"}</Badge>
            </span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export function Landing() {
  return (
    <>
      <section className="container-page grid gap-10 py-14 lg:grid-cols-2 lg:items-center lg:py-20">
        <div>
          <p className="eyebrow">Career intelligence for engineers</p>
          <h1 className="mt-3 font-serif text-4xl leading-tight text-ink sm:text-5xl">
            Understand where you stand. See what each opportunity requires. Build the evidence to get there.
          </h1>
          <p className="mt-5 max-w-prose text-lg text-ink-soft">
            Resumo analyses your resume with transparent, explainable scoring, compares it to real job
            descriptions, and turns the gaps into concrete projects and a week-by-week plan. No black boxes.
            No invented achievements.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link to="/signup">
              <Button size="lg">
                Start free <ArrowRight className="h-4 w-4" aria-hidden />
              </Button>
            </Link>
            <Link to="/how-it-works">
              <Button size="lg" variant="secondary">
                See how it works
              </Button>
            </Link>
          </div>
          <p className="mt-4 text-xs text-ink-muted">
            Works with your own resume in PDF, DOCX, LaTeX and more. Optional local AI — nothing leaves your
            machine unless you configure it.
          </p>
        </div>
        <DemoAnalysis />
      </section>

      <section className="border-y border-stone-200 bg-ivory-50">
        <div className="container-page grid gap-8 py-12 sm:grid-cols-3">
          {[
            { icon: FileText, title: "Explainable resume review", body: "Category scores with the exact excerpts and reasons behind every finding." },
            { icon: Target, title: "Evidence-backed matching", body: "A keyword table that separates a real missing skill from a missing keyword." },
            { icon: Sparkles, title: "Gaps become projects", body: "Each gap maps to an achievable project brief and the evidence to publish." },
          ].map((f) => (
            <div key={f.title}>
              <f.icon className="h-5 w-5 text-forest" aria-hidden />
              <h3 className="mt-3 font-serif text-lg">{f.title}</h3>
              <p className="mt-1 text-sm text-ink-muted">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="container-page py-14">
        <p className="eyebrow">The workflow</p>
        <h2 className="mt-2 max-w-2xl font-serif text-3xl">
          From a rough resume to a portfolio that proves your skills
        </h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Upload or build", "Import PDF, DOCX, LaTeX, RTF and more, or start from a clean template."],
            ["Analyse honestly", "Deterministic scoring flags weak verbs, missing sections and ATS risks."],
            ["Match to a role", "Paste a job description; see evidenced skills versus real gaps."],
            ["Close the gap", "Get a roadmap, project briefs and portfolio assets tied to the job."],
          ].map(([title, body], i) => (
            <Card key={title}>
              <span className="font-serif text-2xl text-forest">{i + 1}</span>
              <h3 className="mt-2 font-medium text-ink">{title}</h3>
              <p className="mt-1 text-sm text-ink-muted">{body}</p>
            </Card>
          ))}
        </div>
      </section>

      <section className="border-t border-stone-200 bg-ivory-50">
        <div className="container-page grid gap-10 py-14 lg:grid-cols-2">
          <div>
            <p className="eyebrow">Transparent by design</p>
            <h2 className="mt-2 font-serif text-3xl">How scoring actually works</h2>
            <div className="mt-5 space-y-3 text-sm text-ink-soft">
              <p className="flex gap-2">
                <Search className="mt-0.5 h-4 w-4 shrink-0 text-forest" aria-hidden />
                Scores are produced by deterministic rules over your structured resume — grammar signals, weak
                verbs, impact wording, section coverage and ATS risks.
              </p>
              <p className="flex gap-2">
                <Search className="mt-0.5 h-4 w-4 shrink-0 text-forest" aria-hidden />
                AI, when enabled, adds separately labelled commentary. It never changes your deterministic score,
                and it never invents facts.
              </p>
              <p className="flex gap-2">
                <Search className="mt-0.5 h-4 w-4 shrink-0 text-forest" aria-hidden />
                We never claim a "guaranteed ATS pass" or an interview probability. Resumo is advisory.
              </p>
            </div>
          </div>
          <Card>
            <h3 className="font-serif text-lg">A student's path, not a checklist</h3>
            <ul className="mt-3 space-y-3 text-sm text-ink-soft">
              <li className="flex gap-2">
                <Check className="mt-0.5 h-4 w-4 text-forest" aria-hidden />
                Missing <strong className="font-medium">Docker</strong>? Resumo suggests a small containerised API
                project — not "learn everything."
              </li>
              <li className="flex gap-2">
                <Check className="mt-0.5 h-4 w-4 text-forest" aria-hidden />
                Each project brief explains which job requirement it demonstrates and what evidence to publish.
              </li>
              <li className="flex gap-2">
                <Check className="mt-0.5 h-4 w-4 text-forest" aria-hidden />
                Milestones carry resources and completion tracking so the plan adapts as you progress.
              </li>
            </ul>
          </Card>
        </div>
      </section>

      <section className="container-page py-16 text-center">
        <h2 className="font-serif text-3xl">Build evidence, not buzzwords</h2>
        <p className="mx-auto mt-3 max-w-xl text-ink-muted">
          Create an account and upload your resume. Resumo will show you exactly what to fix and what to build next.
        </p>
        <Link to="/signup" className="mt-6 inline-block">
          <Button size="lg">
            Get started <ArrowRight className="h-4 w-4" aria-hidden />
          </Button>
        </Link>
      </section>
    </>
  );
}
