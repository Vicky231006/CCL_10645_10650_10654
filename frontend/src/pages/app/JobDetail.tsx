import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { Target } from "lucide-react";
import { api } from "../../lib/api";
import type { Job } from "../../lib/types";
import { Badge, Button, Card, SectionHeading, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { formatDate } from "../../lib/utils";

const parsedKeys: [string, string][] = [
  ["required_skills", "Required skills"],
  ["preferred_skills", "Preferred skills"],
  ["tools", "Tools & technologies"],
  ["responsibilities", "Responsibilities"],
  ["qualifications", "Qualifications"],
  ["domain", "Domain / industry"],
  ["certifications", "Certifications"],
  ["terminology", "Notable terminology"],
];

export function JobDetail() {
  const { id = "" } = useParams();
  const query = useQuery({ queryKey: ["job", id], queryFn: () => api.get<Job>(`/jobs/${id}`) });

  if (query.isLoading) return <Spinner label="Loading job description" />;
  if (query.isError || !query.data) return <Card><p className="text-sm text-clay">Could not load this job description.</p></Card>;
  const job = query.data;
  const parsed = job.parsed as Record<string, unknown>;

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        title={job.title}
        description={[job.company, job.location].filter(Boolean).join(" · ") || "No company given"}
        action={
          <Link to={`/app/match?job=${job.id}`}>
            <Button>
              <Target className="h-4 w-4" aria-hidden /> Match a resume
            </Button>
          </Link>
        }
      />

      <div className="mb-6 flex flex-wrap gap-2">
        {job.seniority && <Badge tone="neutral">{job.seniority}</Badge>}
        {job.opportunity_type && <Badge tone="info">{job.opportunity_type.replace(/_/g, " ")}</Badge>}
        {typeof parsed.experience_years === "string" && parsed.experience_years && <Badge tone="neutral">{parsed.experience_years}</Badge>}
        <span className="text-xs text-ink-muted">Added {formatDate(job.created_at)}</span>
      </div>

      <Card className="mb-6">
        <SectionHeading title="Parsed requirements" description="Extracted deterministically from the posting text. Preferred vs required drives how gaps are weighted." />
        <dl className="grid gap-4 sm:grid-cols-2">
          {parsedKeys.map(([key, label]) => {
            const value = parsed[key];
            if (!Array.isArray(value) || value.length === 0) return null;
            return (
              <div key={key}>
                <dt className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{label}</dt>
                <dd className="mt-1.5 flex flex-wrap gap-1.5">
                  {value.map((v) => (
                    <Badge key={String(v)} tone={key === "required_skills" ? "positive" : "neutral"}>
                      {String(v)}
                    </Badge>
                  ))}
                </dd>
              </div>
            );
          })}
        </dl>
      </Card>

      <Card>
        <SectionHeading title="Original text" description="Exactly what you pasted — the source of truth for matching." />
        <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-ivory-100 p-4 text-sm leading-6 text-ink-soft">
          {job.raw_text}
        </pre>
      </Card>
    </div>
  );
}
