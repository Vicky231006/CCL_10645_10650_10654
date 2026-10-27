import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, ExternalLink, Plus } from "lucide-react";
import { Alert, Badge, Button, Card, EmptyState, Field, Input, SectionHeading, Spinner, Textarea } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { api, ApiError } from "../../lib/api";
import type { CompanyResearch } from "../../lib/types";
import { formatDate } from "../../lib/utils";

export function CompanyInsights() {
  const qc = useQueryClient();
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [urls, setUrls] = useState("");
  const [useAi, setUseAi] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<CompanyResearch | null>(null);

  const list = useQuery({ queryKey: ["company"], queryFn: () => api.get<CompanyResearch[]>("/company") });

  useEffect(() => {
    if (!selected && list.data?.length) setSelected(list.data[0]);
  }, [list.data, selected]);

  const create = useMutation({
    mutationFn: () =>
      api.post<CompanyResearch>("/company", {
        company,
        target_role: role || null,
        source_urls: urls.split(/\s+/).map((s) => s.trim()).filter(Boolean),
        use_ai: useAi,
      }),
    onSuccess: (r) => {
      setSelected(r);
      setError(null);
      qc.invalidateQueries({ queryKey: ["company"] });
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not run the research."),
  });

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader title="Company insights" description="Research themes and interview patterns, grounded in the sources you provide. No scraping or private data." />

      <Card className="mb-6">
        <SectionHeading title="New research" description="Paste official careers/interview pages. Findings cite their sources." />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Company" required htmlFor="ci-company">
            <Input id="ci-company" value={company} onChange={(e) => setCompany(e.target.value)} placeholder="Acme Corp" />
          </Field>
          <Field label="Target role (optional)" htmlFor="ci-role">
            <Input id="ci-role" value={role} onChange={(e) => setRole(e.target.value)} placeholder="SDE Intern" />
          </Field>
        </div>
        <div className="mt-4">
          <Field label="Source URLs" hint="One per line or space-separated. Public pages only." htmlFor="ci-urls">
            <Textarea id="ci-urls" rows={3} value={urls} onChange={(e) => setUrls(e.target.value)} placeholder="https://acme.com/careers" />
          </Field>
        </div>
        <label className="mt-3 flex items-center gap-2 text-sm text-ink-soft">
          <input type="checkbox" checked={useAi} onChange={(e) => setUseAi(e.target.checked)} /> Use AI synthesis (optional)
        </label>
        {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
        <div className="mt-4">
          <Button onClick={() => create.mutate()} loading={create.isPending} disabled={!company.trim()}>
            <Plus className="h-4 w-4" aria-hidden /> Generate insights
          </Button>
        </div>
      </Card>

      {list.isLoading ? (
        <Spinner label="Loading research" />
      ) : !selected ? (
        <EmptyState title="No research yet" description="Generate insights to prepare themes and questions for a specific company." />
      ) : (
        <div className="grid gap-6 md:grid-cols-[16rem,1fr]">
          <aside>
            <p className="eyebrow mb-2">Saved</p>
            <ul className="space-y-1">
              {list.data?.map((r) => (
                <li key={r.id}>
                  <button
                    onClick={() => setSelected(r)}
                    className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm ${r.id === selected.id ? "bg-forest-tint text-forest" : "text-ink-soft hover:bg-ivory-200"}`}
                  >
                    <Building2 className="h-4 w-4 shrink-0" aria-hidden />
                    <span className="truncate">{r.company}</span>
                  </button>
                </li>
              ))}
            </ul>
          </aside>

          <div className="space-y-5">
            <Card>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-serif text-xl">{selected.company}</h2>
                  {selected.target_role && <p className="text-sm text-ink-muted">{selected.target_role}</p>}
                </div>
                <Badge tone={selected.confidence === "high" ? "positive" : selected.confidence === "low" ? "warning" : "neutral"}>
                  {selected.confidence} confidence
                </Badge>
              </div>
              {selected.summary && <p className="mt-3 text-sm text-ink-soft">{selected.summary}</p>}
              <p className="mt-2 text-xs text-ink-muted">Generated {formatDate(selected.created_at)}</p>

              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <TagSection title="Themes" items={selected.themes} />
                <TagSection title="Interview patterns" items={selected.patterns} />
              </div>
            </Card>

            <Card>
              <SectionHeading title="Sources" description="Every claim should trace to one of these." />
              {selected.citations.length === 0 ? (
                <p className="text-sm text-ink-muted">No citations recorded.</p>
              ) : (
                <ul className="space-y-3">
                  {selected.citations.map((c) => (
                    <li key={c.id} className="rounded-md border border-stone-200 bg-ivory-50 p-3">
                      <a href={c.url} target="_blank" rel="noreferrer noopener" className="inline-flex items-center gap-1 text-sm font-medium text-forest hover:underline">
                        {c.label} <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                      </a>
                      <p className="mt-1 text-xs text-ink-muted">{c.source_type}{c.retrieved_at ? ` · retrieved ${c.retrieved_at}` : ""}</p>
                      {c.excerpt && <p className="mt-1 text-sm text-ink-soft">{c.excerpt}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function TagSection({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{title}</p>
      {items.length === 0 ? (
        <p className="mt-1.5 text-sm text-ink-muted">None identified</p>
      ) : (
        <ul className="mt-1.5 space-y-1 text-sm text-ink-soft">
          {items.map((i) => <li key={i}>{i}</li>)}
        </ul>
      )}
    </div>
  );
}
