import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { Alert, Badge, Button, Card, EmptyState, Field, Select, SectionHeading, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { api, ApiError } from "../../lib/api";
import type { Job, Match, Paged, Resume } from "../../lib/types";
import { ScoreDial } from "../../components/Score";
import { formatDate } from "../../lib/utils";

const statusTone = { found: "positive", weak: "warning", missing: "critical" } as const;

export function MatchPage() {
  const [params, setParams] = useSearchParams();
  const qc = useQueryClient();
  const [jobId, setJobId] = useState(params.get("job") ?? "");
  const [resumeId, setResumeId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Match | null>(null);

  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => api.get<Paged<Job>>("/jobs") });
  const resumes = useQuery({ queryKey: ["resumes"], queryFn: () => api.get<Paged<Resume>>("/resumes") });
  const matches = useQuery({ queryKey: ["matches"], queryFn: () => api.get<Paged<Match>>("/matches") });

  useEffect(() => {
    if (!resumeId && resumes.data?.items.length) setResumeId(resumes.data.items[0].id);
  }, [resumes.data, resumeId]);

  const run = useMutation({
    mutationFn: () => api.post<Match>("/jobs/match", { job_id: jobId, resume_id: resumeId }),
    onSuccess: (m) => {
      setResult(m);
      setError(null);
      qc.invalidateQueries({ queryKey: ["matches"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Matching failed."),
  });

  const canRun = jobId && resumeId;

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Match & keywords" description="Transparent, evidence-based alignment between one resume version and a job description." />

      <Card className="mb-6">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Job description" htmlFor="m-job">
            <Select
              id="m-job"
              value={jobId}
              onChange={(e) => {
                setJobId(e.target.value);
                setParams(e.target.value ? { job: e.target.value } : {});
              }}
            >
              <option value="">Select a job description…</option>
              {jobs.data?.items.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title}
                  {j.company ? ` — ${j.company}` : ""}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Resume" htmlFor="m-resume">
            <Select id="m-resume" value={resumeId} onChange={(e) => setResumeId(e.target.value)}>
              <option value="">Select a resume…</option>
              {resumes.data?.items.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.title}
                </option>
              ))}
            </Select>
          </Field>
        </div>
        {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Button onClick={() => run.mutate()} loading={run.isPending} disabled={!canRun}>
            Run match
          </Button>
          {!jobs.data?.items.length && <span className="text-xs text-ink-muted">Add a job description first.</span>}
          {!resumes.data?.items.length && <span className="text-xs text-ink-muted">Upload a resume first.</span>}
        </div>
      </Card>

      {result && (
        <div className="mb-6 space-y-5">
          <Card>
            <div className="flex flex-wrap items-center gap-6">
              <ScoreDial value={result.overall_score} max={100} label="Alignment" size={130} />
              <div>
                <p className="eyebrow">Weighted coverage</p>
                <p className="mt-1 text-sm text-ink-soft">
                  {result.coverage != null ? `${Math.round(result.coverage * 100)}% of weighted requirements` : "—"}
                </p>
                {result.methodology && <p className="mt-2 max-w-prose text-xs text-ink-muted">{result.methodology}</p>}
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link to={`/app/career-roadmap?job=${result.job_id}&resume=${result.resume_id}`}>
                <Button variant="secondary">Build a roadmap from these gaps</Button>
              </Link>
            </div>
          </Card>

          <div>
            <SectionHeading title="Keyword evidence" description="Where each requirement is (or isn't) evidenced in your resume." />
            <div className="overflow-hidden rounded-lg border border-stone-200">
              <table className="w-full text-left text-sm">
                <thead className="bg-ivory-200 text-xs uppercase tracking-wide text-ink-muted">
                  <tr>
                    <th className="px-3 py-2 font-medium">Keyword</th>
                    <th className="px-3 py-2 font-medium">Importance</th>
                    <th className="px-3 py-2 font-medium">Status</th>
                    <th className="hidden px-3 py-2 font-medium sm:table-cell">Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-200 bg-ivory-50">
                  {result.keywords.map((k) => (
                    <tr key={k.id}>
                      <td className="px-3 py-2 font-medium text-ink">{k.keyword}</td>
                      <td className="px-3 py-2 text-ink-muted">{k.importance}</td>
                      <td className="px-3 py-2">
                        <Badge tone={statusTone[k.status]}>{k.status}</Badge>
                      </td>
                      <td className="hidden px-3 py-2 text-ink-muted sm:table-cell">
                        {k.evidence_excerpt ? (
                          <span>
                            <span className="text-ink-soft">{k.evidence_location}: </span>
                            {k.evidence_excerpt}
                          </span>
                        ) : (
                          k.recommended_action ?? "Not found"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      <div className="mt-8">
        <SectionHeading title="Recent matches" />
        {matches.isLoading ? (
          <Spinner label="Loading matches" />
        ) : matches.data && matches.data.items.length ? (
          <ul className="space-y-2">
            {matches.data.items.map((m) => (
              <li key={m.id}>
                <button
                  onClick={() => setResult(m)}
                  className="card flex w-full items-center justify-between p-4 text-left hover:bg-ivory-50"
                >
                  <span className="text-sm text-ink-soft">
                    {m.overall_score != null ? `${m.overall_score}%` : "—"} · {m.keywords.length} keywords · {formatDate(m.created_at)}
                  </span>
                  <span className="text-xs text-ink-muted">View</span>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="No matches yet" description="Run a match to see exactly which requirements your resume evidences." />
        )}
      </div>
    </div>
  );
}
