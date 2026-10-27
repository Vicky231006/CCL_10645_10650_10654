import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { ExternalLink, Plus } from "lucide-react";
import { Alert, Badge, Button, Card, EmptyState, Field, Input, Progress, SectionHeading, Select, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { api, ApiError } from "../../lib/api";
import type { Job, Paged, Resume, Roadmap } from "../../lib/types";
import { ScoreDial } from "../../components/Score";
import { formatDate } from "../../lib/utils";

export function CareerRoadmap() {
  const [params] = useSearchParams();
  const qc = useQueryClient();
  const [jobId, setJobId] = useState(params.get("job") ?? "");
  const [resumeId, setResumeId] = useState(params.get("resume") ?? "");
  const [targetRole, setTargetRole] = useState("");
  const [company, setCompany] = useState("");
  const [useAi, setUseAi] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<Roadmap | null>(null);

  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => api.get<Paged<Job>>("/jobs") });
  const resumes = useQuery({ queryKey: ["resumes"], queryFn: () => api.get<Paged<Resume>>("/resumes") });
  const roadmaps = useQuery({ queryKey: ["roadmaps"], queryFn: () => api.get<Paged<Roadmap>>("/roadmaps") });

  useEffect(() => {
    if (!resumeId && resumes.data?.items.length) setResumeId(resumes.data.items[0].id);
  }, [resumes.data, resumeId]);

  useEffect(() => {
    if (!active && roadmaps.data?.items.length) setActive(roadmaps.data.items[0]);
  }, [roadmaps.data, active]);

  const create = useMutation({
    mutationFn: () =>
      api.post<Roadmap>("/roadmaps", {
        target_role: targetRole,
        company: company || null,
        job_id: jobId || null,
        resume_id: resumeId || null,
        use_ai: useAi,
      }),
    onSuccess: (r) => {
      setActive(r);
      setError(null);
      qc.invalidateQueries({ queryKey: ["roadmaps"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not build a roadmap."),
  });

  const updateMilestone = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => api.patch(`/milestones/${id}`, { status }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["roadmaps"] });
    },
  });

  const canCreate = targetRole.trim().length > 0 || jobId;

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Career roadmap" description="Turn genuine gaps into a prioritised, achievable plan. Every milestone cites the requirement behind it." />

      <Card className="mb-6">
        <SectionHeading title="Build a roadmap" description="Choose a job description (recommended) or just name a target role." />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Target role" required={!jobId} htmlFor="ro-role">
            <Input id="ro-role" value={targetRole} onChange={(e) => setTargetRole(e.target.value)} placeholder="Backend Intern" />
          </Field>
          <Field label="Company (optional)" htmlFor="ro-company">
            <Input id="ro-company" value={company} onChange={(e) => setCompany(e.target.value)} />
          </Field>
          <Field label="Job description (optional)" htmlFor="ro-job">
            <Select id="ro-job" value={jobId} onChange={(e) => setJobId(e.target.value)}>
              <option value="">None</option>
              {jobs.data?.items.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                  {j.company ? ` — ${j.company}` : ""}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Resume" htmlFor="ro-resume">
            <Select id="ro-resume" value={resumeId} onChange={(e) => setResumeId(e.target.value)}>
              <option value="">Most recent</option>
              {resumes.data?.items.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        <label className="mt-4 flex items-center gap-2 text-sm text-ink-soft">
          <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} />
          Use AI to enrich the analysis (optional)
        </label>
        {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
        <div className="mt-4">
          <Button onClick={() => create.mutate()} loading={create.isPending} disabled={!canCreate}>
            <Plus className="h-4 w-4" aria-hidden /> Build roadmap
          </Button>
        </div>
      </Card>

      {roadmaps.isLoading ? (
        <Spinner label="Loading roadmaps" />
      ) : !active ? (
        <EmptyState title="No roadmap yet" description="Build your first roadmap to see readiness, gaps and a weekly plan." />
      ) : (
        <div className="space-y-6">
          <Card>
            <div className="flex flex-wrap items-center gap-6">
              <ScoreDial value={active.readiness_score} max={100} label="Readiness" size={130} />
              <div className="min-w-64 flex-1">
                <h2 className="font-serif text-xl">{active.target_role}</h2>
                {active.company && <p className="text-sm text-ink-muted">{active.company}</p>}
                {active.summary && <p className="mt-2 max-w-prose text-sm text-ink-soft">{active.summary}</p>}
                <p className="mt-2 text-xs text-ink-muted">Created {formatDate(active.created_at)}{active.ai_used ? " · AI-enriched" : ""}</p>
              </div>
            </div>
            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              <GapList title="Demonstrated" items={active.gap_report.demonstrated ?? []} tone="positive" />
              <GapList title="Missing (required)" items={active.gap_report.missing_required ?? []} tone="critical" />
              <GapList title="Worth adding" items={active.gap_report.missing_valuable ?? []} tone="neutral" />
            </div>
          </Card>

          <div>
            <SectionHeading
              title="Plan"
              description="Work through milestones in order. Mark progress as you produce real evidence."
              action={
                <Link to={`/app/projects?roadmap=${active.id}`}>
                  <Button variant="secondary">Create a project for this plan</Button>
                </Link>
              }
            />
            <ol className="space-y-3">
              {active.milestones.map((m) => (
                <li key={m.id}>
                  <Card>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-medium text-ink">{m.title}</h3>
                          <Badge tone="neutral">{m.kind}</Badge>
                          {m.week != null && <Badge tone="info">week {m.week}</Badge>}
                          {m.estimated_hours != null && <Badge tone="neutral">~{m.estimated_hours}h</Badge>}
                        </div>
                        {m.rationale && <p className="mt-1.5 text-sm text-ink-soft">{m.rationale}</p>}
                        {m.source_requirement && (
                          <p className="mt-1 text-xs text-ink-muted">Addresses: {m.source_requirement}</p>
                        )}
                      </div>
                      <Select
                        value={m.status}
                        onChange={(e) => updateMilestone.mutate({ id: m.id, status: e.target.value })}
                        className="w-32"
                        aria-label={`Status for ${m.title}`}
                      >
                        <option value="todo">To do</option>
                        <option value="in_progress">In progress</option>
                        <option value="done">Done</option>
                      </Select>
                    </div>
                    {m.resources.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {m.resources.map((r) => (
                          <a
                            key={r.id}
                            href={r.url}
                            target="_blank"
                            rel="noreferrer noopener"
                            className="inline-flex items-center gap-1 rounded-full border border-stone-200 bg-ivory-100 px-2.5 py-0.5 text-xs text-forest hover:bg-ivory-200"
                          >
                            {r.title} {r.is_free && "· free"} <ExternalLink className="h-3 w-3" aria-hidden />
                          </a>
                        ))}
                      </div>
                    )}
                    {m.status === "done" && (
                      <Progress value={100} label="Completed" />
                    )}
                  </Card>
                </li>
              ))}
            </ol>
          </div>

          {(roadmaps.data?.items.length ?? 0) > 1 && (
            <div>
              <SectionHeading title="Other roadmaps" />
              <div className="flex flex-wrap gap-2">
                {roadmaps.data?.items.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => setActive(r)}
                    className={`rounded-md border px-3 py-1.5 text-sm ${r.id === active.id ? "border-forest bg-forest-tint text-forest" : "border-stone-300 text-ink-soft hover:bg-ivory-200"}`}
                  >
                    {r.target_role}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function GapList({ title, items, tone }: { title: string; items: string[]; tone: "positive" | "critical" | "neutral" }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{title}</p>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-ink-muted">None</p>
      ) : (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {items.map((i) => (
            <Badge key={i} tone={tone}>
              {i}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
