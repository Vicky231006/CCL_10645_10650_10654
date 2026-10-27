import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { api, ApiError } from "../../lib/api";
import type { AiStatus, Analysis, Resume } from "../../lib/types";
import { Alert, Badge, Button, Card, EmptyState, Field, SectionHeading, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { ScoreDial, ScoreBar } from "../../components/Score";
import { formatDate } from "../../lib/utils";

const severityTone: Record<string, "warning" | "info" | "neutral"> = {
  critical: "warning",
  important: "info",
  polish: "neutral",
};

export function ResumeAnalyze() {
  const { id: resumeId = "" } = useParams();
  const qc = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [targetRole, setTargetRole] = useState("");

  const resume = useQuery({ queryKey: ["resume", resumeId], queryFn: () => api.get<Resume>(`/resumes/${resumeId}`) });
  const ai = useQuery({ queryKey: ["ai-status"], queryFn: () => api.get<AiStatus>("/meta/ai-status"), staleTime: 60_000 });
  const analyses = useQuery({ queryKey: ["analyses", resumeId], queryFn: () => api.get<Analysis[]>(`/resumes/${resumeId}/analyses`) });

  const run = useMutation({
    mutationFn: (useAi: boolean) =>
      api.post<Analysis>(`/resumes/${resumeId}/analyze`, { use_ai: useAi, target_role: targetRole || undefined }),
    onSuccess: () => {
      setError(null);
      qc.invalidateQueries({ queryKey: ["analyses", resumeId] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Analysis failed."),
  });

  const latest = analyses.data?.[0];
  const aiAvailable = ai.data?.available && ai.data.configured !== "none";

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title="Quality analysis"
        description={`${resume.data?.title ?? "Resume"} — deterministic scoring with exact excerpts and fixes.`}
        action={
          <Link to={`/app/resumes/${resumeId}`} className="text-sm link-quiet">
            Back to editor
          </Link>
        }
      />

      <Card className="mb-6">
        <div className="flex flex-wrap items-end gap-4">
          <div className="min-w-56 flex-1">
            <Field label="Target role (optional)" hint="Tailors the advice to a specific role." htmlFor="role">
              <input
                id="role"
                className="input"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="Backend Intern"
              />
            </Field>
          </div>
          <Button onClick={() => run.mutate(false)} loading={run.isPending && !run.variables}>
            <Sparkles className="h-4 w-4" aria-hidden /> Run analysis
          </Button>
          {aiAvailable && (
            <Button variant="secondary" onClick={() => run.mutate(true)} loading={run.isPending && run.variables === true}>
              Run with AI commentary
            </Button>
          )}
        </div>
        {!aiAvailable && (
          <p className="mt-3 text-xs text-ink-muted">
            AI commentary is off ({ai.data?.configured ?? "unavailable"}). Deterministic analysis fully works without it.
          </p>
        )}
        {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
      </Card>

      {analyses.isLoading ? (
        <Spinner label="Loading analyses" />
      ) : !latest ? (
        <EmptyState
          title="No analysis yet"
          description="Run an analysis to see category scores, severity-ranked findings, and specific suggested fixes."
        />
      ) : (
        <div className="space-y-6">
          <Card>
            <div className="flex flex-wrap items-center gap-6">
              <ScoreDial value={latest.overall_score} label="Overall" />
              <div className="min-w-64 flex-1 space-y-2">
                {Object.entries(latest.category_scores).map(([cat, score]) => (
                  <ScoreBar key={cat} label={cat.replace(/_/g, " ")} value={score} />
                ))}
              </div>
            </div>
            {latest.methodology && <p className="mt-4 text-xs text-ink-muted">{latest.methodology}</p>}
            <p className="mt-1 text-xs text-ink-muted">
              Advisory score from transparent rules — not an employer ATS score. Analysed {formatDate(latest.created_at)}.
              {latest.ai_used ? " AI commentary included." : ""}
            </p>
          </Card>

          {latest.ai_commentary && (
            <Card className="bg-forest-tint">
              <SectionHeading title="AI commentary" description="Generated guidance — verify before acting." />
              <pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-ink-soft">{latest.ai_commentary}</pre>
            </Card>
          )}

          <div>
            <SectionHeading title="Findings" description={`${latest.findings.length} item(s), most severe first.`} />
            {latest.findings.length === 0 ? (
              <Card><p className="text-sm text-forest-dark">No issues detected by the current rules. Still proofread before sending.</p></Card>
            ) : (
              <ul className="space-y-3">
                {latest.findings.map((f) => (
                  <li key={f.id}>
                    <Card>
                      <div className="flex items-start justify-between gap-3">
                        <h3 className="font-medium text-ink">{f.title}</h3>
                        <Badge tone={severityTone[f.severity] ?? "neutral"}>{f.severity}</Badge>
                      </div>
                      {f.excerpt && (
                        <blockquote className="mt-2 border-l-2 border-stone-300 pl-3 text-sm italic text-ink-muted">
                          {f.excerpt}
                        </blockquote>
                      )}
                      {f.explanation && <p className="mt-2 text-sm text-ink-soft">{f.explanation}</p>}
                      {f.suggestion && (
                        <p className="mt-2 text-sm text-forest-dark">
                          <strong className="font-medium">Fix:</strong> {f.suggestion}
                        </p>
                      )}
                      <p className="mt-2 text-xs text-ink-muted">
                        {f.category} · {f.location ?? "document"}
                      </p>
                    </Card>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
