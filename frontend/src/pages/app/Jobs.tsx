import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { Briefcase, Plus } from "lucide-react";
import { api, ApiError } from "../../lib/api";
import type { Job, Paged } from "../../lib/types";
import { Alert, Badge, Button, Card, EmptyState, Field, Input, SectionHeading, Spinner, Textarea } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { formatDate } from "../../lib/utils";

const emptyForm = { title: "", company: "", location: "", source_url: "", raw_text: "", opportunity_type: "" };

export function Jobs() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [error, setError] = useState<string | null>(null);

  const list = useQuery({ queryKey: ["jobs"], queryFn: () => api.get<Paged<Job>>("/jobs") });

  const create = useMutation({
    mutationFn: () =>
      api.post<Job>("/jobs", {
        title: form.title,
        company: form.company || null,
        location: form.location || null,
        source_url: form.source_url || null,
        opportunity_type: form.opportunity_type || null,
        raw_text: form.raw_text,
      }),
    onSuccess: (job) => {
      qc.invalidateQueries({ queryKey: ["jobs"] });
      navigate(`/app/jobs/${job.id}`);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not save the job description."),
  });

  return (
    <div>
      <PageHeader
        title="Job descriptions"
        description="Paste a real posting to extract requirements, then match it against your resume. Nothing is scraped automatically."
        action={
          <Button onClick={() => setShowForm((v) => !v)}>
            <Plus className="h-4 w-4" aria-hidden /> Add description
          </Button>
        }
      />

      {showForm && (
        <Card className="mb-6">
          <SectionHeading title="New job description" description="Minimum 20 characters of description text." />
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Job title" required htmlFor="j-title">
              <Input id="j-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </Field>
            <Field label="Company" htmlFor="j-company">
              <Input id="j-company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            </Field>
            <Field label="Location" htmlFor="j-loc">
              <Input id="j-loc" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
            </Field>
            <Field label="Source URL" htmlFor="j-url">
              <Input id="j-url" value={form.source_url} onChange={(e) => setForm({ ...form, source_url: e.target.value })} placeholder="https://" />
            </Field>
            <Field label="Opportunity type" htmlFor="j-type">
              <Input id="j-type" value={form.opportunity_type} onChange={(e) => setForm({ ...form, opportunity_type: e.target.value })} placeholder="internship / full_time" />
            </Field>
          </div>
          <div className="mt-4">
            <Field label="Description text" required htmlFor="j-text">
              <Textarea id="j-text" rows={8} value={form.raw_text} onChange={(e) => setForm({ ...form, raw_text: e.target.value })} placeholder="Paste the full job description here…" />
            </Field>
          </div>
          {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
          <div className="mt-4 flex gap-2">
            <Button onClick={() => create.mutate()} loading={create.isPending} disabled={!form.title || form.raw_text.length < 20}>
              Save description
            </Button>
            <Button variant="ghost" onClick={() => { setShowForm(false); setForm(emptyForm); setError(null); }}>
              Cancel
            </Button>
          </div>
        </Card>
      )}

      {list.isLoading ? (
        <Spinner label="Loading job descriptions" />
      ) : list.data && list.data.items.length > 0 ? (
        <ul className="grid gap-4 sm:grid-cols-2">
          {list.data.items.map((j) => (
            <li key={j.id}>
              <Link to={`/app/jobs/${j.id}`} className="card flex items-start gap-4 p-5 hover:bg-ivory-50">
                <Briefcase className="mt-0.5 h-5 w-5 text-forest" aria-hidden />
                <div className="min-w-0">
                  <p className="truncate font-medium text-ink">{j.title}</p>
                  <p className="mt-1 text-xs text-ink-muted">
                    {[j.company, j.location].filter(Boolean).join(" · ") || "No company given"} · added {formatDate(j.created_at)}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {j.seniority && <Badge tone="neutral">{j.seniority}</Badge>}
                    {j.opportunity_type && <Badge tone="info">{j.opportunity_type.replace(/_/g, " ")}</Badge>}
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          title="No job descriptions yet"
          description="Add a posting to extract required vs preferred skills and see exactly what your resume does and doesn't evidence."
          action={<Button onClick={() => setShowForm(true)}><Plus className="h-4 w-4" aria-hidden /> Add your first</Button>}
        />
      )}
    </div>
  );
}
