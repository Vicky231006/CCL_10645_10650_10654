import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowRight, FileText, FolderGit2, Route, Target, Send, Bookmark } from "lucide-react";
import { api } from "../../lib/api";
import type { AiStatus, DashboardData } from "../../lib/types";
import { Badge, Card, EmptyState, SectionHeading, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { ScoreDial } from "../../components/Score";
import { formatDate } from "../../lib/utils";

export function Dashboard() {
  const dash = useQuery({ queryKey: ["dashboard"], queryFn: () => api.get<DashboardData>("/dashboard") });
  const ai = useQuery({ queryKey: ["ai-status"], queryFn: () => api.get<AiStatus>("/meta/ai-status"), staleTime: 60_000 });

  if (dash.isLoading) return <Spinner label="Loading your workspace" />;
  if (dash.isError || !dash.data) return <EmptyState title="Could not load your dashboard" description="Please refresh and try again." />;
  const d = dash.data;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description={d.target_role ? `Targeting ${d.target_role}.` : "Your career workspace at a glance."}
        action={
          <Link to="/app/resumes" className="text-sm link-quiet">
            Add a resume
          </Link>
        }
      />

      {ai.data && !ai.data.available && ai.data.configured !== "none" && (
        <Card className="mb-6 border-stone-300 bg-ivory-200">
          <p className="text-sm text-ink-soft">
            <strong className="font-medium">AI provider “{ai.data.configured}” is not reachable.</strong> Deterministic
            parsing, scoring and export still work. Enable the provider to unlock AI commentary, rewriting and
            generation. ({ai.data.detail})
          </p>
        </Card>
      )}

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="flex items-center gap-5 lg:col-span-1">
          <ScoreDial value={d.latest_quality?.score ?? null} label="Quality" />
          <div>
            <p className="eyebrow">Resume quality</p>
            <p className="mt-1 text-sm text-ink-soft">
              {d.latest_quality ? `Last analysed ${formatDate(d.latest_quality.created_at)}` : "No analysis yet"}
            </p>
            <Link to="/app/resumes" className="mt-2 inline-flex items-center gap-1 text-sm link-quiet">
              Review <ArrowRight className="h-3.5 w-3.5" aria-hidden />
            </Link>
          </div>
        </Card>

        <Card>
          <p className="eyebrow">Job alignment</p>
          <p className="mt-2 font-serif text-4xl">{d.latest_match?.score != null ? `${d.latest_match.score}%` : "—"}</p>
          <p className="mt-1 text-sm text-ink-muted">
            {d.latest_match ? `Most recent match ${formatDate(d.latest_match.created_at)}` : "No match reports yet"}
          </p>
        </Card>

        <Card>
          <p className="eyebrow">Roadmap readiness</p>
          <p className="mt-2 font-serif text-4xl">{d.roadmap?.readiness_score != null ? `${d.roadmap.readiness_score}%` : "—"}</p>
          <p className="mt-1 text-sm text-ink-muted">
            {d.roadmap ? `${d.roadmap.pending_milestones} milestone(s) remaining` : "No roadmap yet"}
          </p>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { icon: FileText, label: "Resumes", value: d.resume_count, to: "/app/resumes" },
          { icon: FolderGit2, label: "Active projects", value: d.active_projects, to: "/app/projects" },
          { icon: Bookmark, label: "Saved jobs", value: d.saved_jobs, to: "/app/jobs" },
          { icon: Send, label: "Applications", value: d.applications, to: "/app/applications" },
        ].map((m) => (
          <Link key={m.label} to={m.to} className="card flex items-center gap-3 p-4 hover:bg-ivory-50">
            <m.icon className="h-5 w-5 text-forest" aria-hidden />
            <div>
              <p className="font-serif text-2xl text-ink">{m.value}</p>
              <p className="text-xs text-ink-muted">{m.label}</p>
            </div>
          </Link>
        ))}
      </div>

      <div className="mt-8">
        <SectionHeading title="What to work on next" description={d.note} />
        {d.next_actions.length === 0 ? (
          <Card className="bg-forest-tint">
            <p className="text-sm text-forest-dark">
              You're in good shape. Review your latest match report and keep your roadmap milestones moving.
            </p>
          </Card>
        ) : (
          <ul className="space-y-2">
            {d.next_actions.slice(0, 6).map((a) => (
              <li key={a.href + a.label}>
                <Link to={a.href} className="card flex items-center justify-between p-4 hover:bg-ivory-50">
                  <span className="text-sm text-ink-soft">{a.label}</span>
                  <ArrowRight className="h-4 w-4 text-ink-muted" aria-hidden />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {[
          { to: "/app/match", icon: Target, title: "Compare to a job", body: "Paste a description and see evidenced skills vs real gaps." },
          { to: "/app/career-roadmap", icon: Route, title: "Plan the gaps", body: "Turn gaps into a weekly plan with resources." },
          { to: "/app/portfolio", icon: FolderGit2, title: "Publish evidence", body: "Build honest portfolio assets from your projects." },
        ].map((c) => (
          <Link key={c.to} to={c.to} className="card p-5 hover:bg-ivory-50">
            <c.icon className="h-5 w-5 text-forest" aria-hidden />
            <h3 className="mt-3 font-medium text-ink">{c.title}</h3>
            <p className="mt-1 text-sm text-ink-muted">{c.body}</p>
          </Link>
        ))}
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
        <Badge tone="neutral">Advisory scores</Badge>
        <span>Indicators reflect real activity only. Nothing here is fabricated.</span>
      </div>
    </div>
  );
}
