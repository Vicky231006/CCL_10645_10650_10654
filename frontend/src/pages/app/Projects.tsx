import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { Download, FolderGit2, Plus, Sparkles } from "lucide-react";
import { Alert, Badge, Button, Card, EmptyState, Field, Input, SectionHeading, Spinner, Textarea } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { api, ApiError } from "../../lib/api";
import type { GeneratedAsset, Paged, ProjectPlan } from "../../lib/types";

export function Projects() {
  const [params] = useSearchParams();
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [useAi, setUseAi] = useState(false);
  const [roadmapId] = useState(params.get("roadmap") ?? "");
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ProjectPlan | null>(null);
  const [asset, setAsset] = useState<GeneratedAsset | null>(null);

  const list = useQuery({ queryKey: ["projects"], queryFn: () => api.get<Paged<ProjectPlan>>("/projects") });

  useEffect(() => {
    if (!selected && list.data?.items.length) setSelected(list.data.items[0]);
  }, [list.data, selected]);

  const create = useMutation({
    mutationFn: () => api.post<ProjectPlan>("/projects", { title, roadmap_id: roadmapId || null, use_ai: useAi }),
    onSuccess: (p) => {
      setSelected(p);
      setTitle("");
      setError(null);
      qc.invalidateQueries({ queryKey: ["projects"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create the project plan."),
  });

  const generate = useMutation({
    mutationFn: (kind: string) => api.post<GeneratedAsset>("/assets/generate", { kind, project_plan_id: selected?.id, use_ai: true }),
    onSuccess: (a) => setAsset(a),
  });

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Projects" description="Briefs that close specific gaps. Build them, then publish honest evidence." />

      <Card className="mb-6">
        <SectionHeading title="New project brief" description="Describe the gap you want to close (e.g. 'REST API with auth and tests')." />
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-64 flex-1">
            <Field label="Project focus" htmlFor="p-title">
              <Input id="p-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Containerised REST API with CI" />
            </Field>
          </div>
          <label className="flex items-center gap-2 pb-2 text-sm text-ink-soft">
            <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} /> Use AI
          </label>
          <Button onClick={() => create.mutate()} loading={create.isPending} disabled={!title.trim()}>
            <Plus className="h-4 w-4" aria-hidden /> Create brief
          </Button>
        </div>
        {roadmapId && <p className="mt-2 text-xs text-ink-muted">Linked to roadmap {roadmapId.slice(0, 8)}.</p>}
        {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
      </Card>

      {list.isLoading ? (
        <Spinner label="Loading projects" />
      ) : !selected ? (
        <EmptyState title="No projects yet" description="Create a brief to turn a gap into a concrete, demonstrable deliverable." />
      ) : (
        <div className="grid gap-6 md:grid-cols-[16rem,1fr]">
          <aside>
            <p className="eyebrow mb-2">Your briefs</p>
            <ul className="space-y-1">
              {list.data?.items.map((p) => (
                <li key={p.id}>
                  <button
                    onClick={() => { setSelected(p); setAsset(null); }}
                    className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm ${p.id === selected.id ? "bg-forest-tint text-forest" : "text-ink-soft hover:bg-ivory-200"}`}
                  >
                    <FolderGit2 className="h-4 w-4 shrink-0" aria-hidden />
                    <span className="truncate">{p.title}</span>
                  </button>
                </li>
              ))}
            </ul>
          </aside>

          <div className="space-y-5">
            <Card>
              <div className="flex items-start justify-between gap-3">
                <h2 className="font-serif text-xl">{selected.title}</h2>
                {selected.ai_used && <Badge tone="info">AI-enriched</Badge>}
              </div>
              {selected.problem && <p className="mt-2 text-sm text-ink-soft">{selected.problem}</p>}
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <FeatureList title="Required features" items={selected.required_features} required />
                <FeatureList title="Optional / stretch" items={selected.optional_features} />
                <FeatureList title="Suggested stack" items={selected.suggested_stack} />
                <FeatureList title="Demonstrates" items={selected.demonstrates} />
                <FeatureList title="Evidence to publish" items={selected.evidence_to_publish} />
                <FeatureList title="Milestones" items={selected.milestones} />
              </div>
              {selected.acceptance_criteria.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Acceptance criteria</p>
                  <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm text-ink-soft">
                    {selected.acceptance_criteria.map((c) => <li key={c}>{c}</li>)}
                  </ul>
                </div>
              )}
              {selected.testing && (
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Testing</p>
                  <p className="mt-1 text-sm text-ink-soft">{selected.testing}</p>
                </div>
              )}
              {selected.resume_guidance && (
                <p className="mt-4 rounded-md bg-forest-tint p-3 text-sm text-forest-dark">{selected.resume_guidance}</p>
              )}
            </Card>

            <EvidencePanel projectId={selected.id} />

            <Card>
              <SectionHeading title="Generate honest assets" description="Drafts are assembled from your own inputs and verified project evidence." />
              <div className="flex flex-wrap gap-2">
                {["readme", "case_study", "project_summary", "bio"].map((k) => (
                  <Button key={k} variant="secondary" onClick={() => generate.mutate(k)} loading={generate.isPending && generate.variables === k}>
                    <Sparkles className="h-4 w-4" aria-hidden /> {k.replace(/_/g, " ")}
                  </Button>
                ))}
              </div>
              {asset && (
                <div className="mt-4">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-medium text-ink">{asset.title}</p>
                    <div className="flex items-center gap-2">
                      {asset.ai_used && <Badge tone="info">AI</Badge>}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          const blob = new Blob([asset.content], { type: "text/markdown" });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = `${asset.title.replace(/\s+/g, "_")}.md`;
                          a.click();
                          URL.revokeObjectURL(url);
                        }}
                      >
                        <Download className="h-4 w-4" aria-hidden /> Download
                      </Button>
                    </div>
                  </div>
                  <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-md bg-ivory-100 p-4 text-sm text-ink-soft">{asset.content}</pre>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function FeatureList({ title, items, required }: { title: string; items: string[]; required?: boolean }) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{title}</p>
      <ul className="mt-1.5 space-y-1 text-sm text-ink-soft">
        {items.map((i) => (
          <li key={i} className="flex gap-2">
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${required ? "bg-forest" : "bg-stone-300"}`} aria-hidden />
            {i}
          </li>
        ))}
      </ul>
    </div>
  );
}

function EvidencePanel({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: "", problem: "", contribution: "", outcomes: "", repo_url: "", stack: "" });

  const evidence = useQuery({
    queryKey: ["evidence", projectId],
    queryFn: () => api.get<{ id: string; title: string; outcomes: string | null; repo_url: string | null }[]>(`/projects/${projectId}/evidence`),
  });

  const add = useMutation({
    mutationFn: () =>
      api.post(`/projects/${projectId}/evidence`, {
        title: form.title,
        problem: form.problem || null,
        contribution: form.contribution || null,
        outcomes: form.outcomes || null,
        repo_url: form.repo_url || null,
        stack: form.stack.split(",").map((s) => s.trim()).filter(Boolean),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["evidence", projectId] });
      setForm({ title: "", problem: "", contribution: "", outcomes: "", repo_url: "", stack: "" });
      setOpen(false);
    },
  });

  return (
    <Card>
      <SectionHeading
        title="Project evidence"
        description="Record only what you actually built. This powers truthful portfolio and resume content."
        action={<Button variant="secondary" onClick={() => setOpen((v) => !v)}>Add evidence</Button>}
      />
      {open && (
        <div className="mb-4 grid gap-3 sm:grid-cols-2">
          <Field label="Title" required><Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></Field>
          <Field label="Repo URL"><Input value={form.repo_url} onChange={(e) => setForm({ ...form, repo_url: e.target.value })} placeholder="https://github.com/…" /></Field>
          <Field label="Stack"><Input value={form.stack} onChange={(e) => setForm({ ...form, stack: e.target.value })} placeholder="FastAPI, Postgres" /></Field>
          <Field label="Outcomes" hint="Real, verifiable outcomes only"><Input value={form.outcomes} onChange={(e) => setForm({ ...form, outcomes: e.target.value })} /></Field>
          <div className="sm:col-span-2">
            <Field label="Problem"><Textarea rows={2} value={form.problem} onChange={(e) => setForm({ ...form, problem: e.target.value })} /></Field>
          </div>
          <div className="sm:col-span-2">
            <Field label="Your contribution"><Textarea rows={2} value={form.contribution} onChange={(e) => setForm({ ...form, contribution: e.target.value })} /></Field>
          </div>
          <div className="sm:col-span-2">
            <Button onClick={() => add.mutate()} loading={add.isPending} disabled={!form.title.trim()}>Save evidence</Button>
          </div>
        </div>
      )}
      {evidence.data && evidence.data.length > 0 ? (
        <ul className="space-y-2">
          {evidence.data.map((e) => (
            <li key={e.id} className="rounded-md border border-stone-200 bg-ivory-50 p-3">
              <p className="text-sm font-medium text-ink">{e.title}</p>
              {e.outcomes && <p className="text-sm text-ink-soft">{e.outcomes}</p>}
              {e.repo_url && <p className="mt-1 text-xs text-forest">{e.repo_url}</p>}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-ink-muted">No evidence recorded yet.</p>
      )}
    </Card>
  );
}
