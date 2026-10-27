import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { Alert, Button, Card, EmptyState, Field, Input, SectionHeading, Select, Spinner, Textarea } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { api, ApiError } from "../../lib/api";
import type { Application, Paged } from "../../lib/types";
import { formatDate } from "../../lib/utils";

const STATUSES = ["saved", "applied", "interview", "offer", "rejected", "withdrawn"] as const;
const statusTone: Record<string, string> = {
  saved: "border-stone-300",
  applied: "border-forest/40",
  interview: "border-forest/60",
  offer: "border-forest",
  rejected: "border-clay/50",
  withdrawn: "border-stone-200",
};

export function Applications() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ company: "", role: "", job_url: "", source: "", cover_letter: "", contact_notes: "" });

  const list = useQuery({ queryKey: ["applications"], queryFn: () => api.get<Paged<Application>>("/applications") });

  const create = useMutation({
    mutationFn: () => api.post<Application>("/applications", { ...form, status: "saved" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      setForm({ company: "", role: "", job_url: "", source: "", cover_letter: "", contact_notes: "" });
      setOpen(false);
      setError(null);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not add the application."),
  });

  const update = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => api.patch(`/applications/${id}`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["applications"] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.del(`/applications/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["applications"] }),
  });

  const byStatus = (status: string) => list.data?.items.filter((a) => a.status === status) ?? [];

  return (
    <div>
      <PageHeader
        title="Applications"
        description="Track every application next to the resume, match and roadmap behind it."
        action={<Button onClick={() => setOpen((v) => !v)}><Plus className="h-4 w-4" aria-hidden /> Add application</Button>}
      />

      {open && (
        <Card className="mb-6">
          <SectionHeading title="New application" />
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Company" required><Input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} /></Field>
            <Field label="Role" required><Input value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} /></Field>
            <Field label="Job URL"><Input value={form.job_url} onChange={(e) => setForm({ ...form, job_url: e.target.value })} placeholder="https://" /></Field>
            <Field label="Source"><Input value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} placeholder="LinkedIn, referral…" /></Field>
            <div className="sm:col-span-2">
              <Field label="Contact notes"><Textarea rows={2} value={form.contact_notes} onChange={(e) => setForm({ ...form, contact_notes: e.target.value })} /></Field>
            </div>
          </div>
          {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
          <div className="mt-4 flex gap-2">
            <Button onClick={() => create.mutate()} loading={create.isPending} disabled={!form.company.trim() || !form.role.trim()}>Save</Button>
            <Button variant="ghost" onClick={() => setOpen(false)}>Cancel</Button>
          </div>
        </Card>
      )}

      {list.isLoading ? (
        <Spinner label="Loading applications" />
      ) : !list.data?.items.length ? (
        <EmptyState title="No applications yet" description="Add roles you're pursuing to keep resumes, matches and notes together." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-3 xl:grid-cols-6">
          {STATUSES.map((status) => (
            <div key={status} className="min-w-0">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{status}</p>
                <span className="text-xs text-ink-faint">{byStatus(status).length}</span>
              </div>
              <div className="space-y-2">
                {byStatus(status).map((a) => (
                  <div key={a.id} className={`rounded-md border-l-4 border border-stone-200 bg-ivory-50 p-3 ${statusTone[a.status]}`}>
                    <p className="truncate text-sm font-medium text-ink">{a.role}</p>
                    <p className="truncate text-xs text-ink-muted">{a.company}</p>
                    <p className="mt-1 text-[11px] text-ink-faint">{formatDate(a.created_at)}</p>
                    <div className="mt-2 flex items-center gap-1">
                      <Select
                        value={a.status}
                        onChange={(e) => update.mutate({ id: a.id, status: e.target.value })}
                        className="h-7 py-0 text-xs"
                        aria-label={`Status for ${a.role}`}
                      >
                        {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                      </Select>
                      <button type="button" className="btn-icon" onClick={() => remove.mutate(a.id)} aria-label="Delete application">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
