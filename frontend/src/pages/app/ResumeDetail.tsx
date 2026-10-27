import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowDown, ArrowUp, Copy, Download, Plus, Sparkles, Trash2 } from "lucide-react";
import { api, downloadFile } from "../../lib/api";
import { ensureUrl } from "../../lib/utils";
import type { Resume, ResumeContent, ExperienceItem, ProjectItem, EducationItem, LinkItem } from "../../lib/types";
import { Alert, Badge, Button, Card, Field, Input, Select, Spinner, Textarea } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { ResumePreview } from "../../components/ResumePreview";

type SaveState = "idle" | "saving" | "saved" | "error";

const SECTIONS = ["summary", "experience", "projects", "education", "skills", "certifications", "achievements"] as const;

export function ResumeDetail() {
  const { id: resumeId = "" } = useParams();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const query = useQuery({ queryKey: ["resume", resumeId], queryFn: () => api.get<Resume>(`/resumes/${resumeId}`) });

  const [content, setContent] = useState<ResumeContent | null>(null);
  const [title, setTitle] = useState("");
  const [pageSize, setPageSize] = useState("A4");
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [exporting, setExporting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const hydrated = useRef(false);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    if (query.data && !hydrated.current) {
      hydrated.current = true;
      setContent((query.data.latest_version?.content as ResumeContent) ?? null);
      setTitle(query.data.title);
      setPageSize(query.data.page_size);
    }
  }, [query.data]);

  const save = useMutation({
    mutationFn: (payload: Record<string, unknown>) => api.patch<Resume>(`/resumes/${resumeId}`, payload),
    onMutate: () => setSaveState("saving"),
    onSuccess: () => {
      setSaveState("saved");
      qc.invalidateQueries({ queryKey: ["resumes"] });
      setTimeout(() => setSaveState((s) => (s === "saved" ? "idle" : s)), 1500);
    },
    onError: () => setSaveState("error"),
  });

  function queueSave(patch: Record<string, unknown>) {
    if (!hydrated.current) return;
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => save.mutate(patch), 800);
  }

  function update(next: ResumeContent) {
    setContent(next);
    queueSave({ content: next });
  }

  const remove = useMutation({
    mutationFn: () => api.del(`/resumes/${resumeId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["resumes"] });
      navigate("/app/resumes");
    },
  });

  const duplicate = useMutation({
    mutationFn: () => api.post<Resume>(`/resumes/${resumeId}/duplicate`),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ["resumes"] });
      navigate(`/app/resumes/${r.id}`);
    },
  });

  async function runExport(format: string) {
    setError(null);
    setExporting(format);
    try {
      const ext = format === "latex" ? "tex" : format;
      await downloadFile(`/resumes/${resumeId}/export`, { format, page_size: pageSize }, `${title || "resume"}.${ext}`);
    } catch {
      setError("Export failed. Please try again.");
    } finally {
      setExporting(null);
    }
  }

  const moveSection = useMemo(
    () => (key: string, dir: -1 | 1) => {
      if (!content) return;
      const order = [...(content.section_order?.length ? content.section_order : SECTIONS)];
      const i = order.indexOf(key);
      const j = i + dir;
      if (i < 0 || j < 0 || j >= order.length) return;
      [order[i], order[j]] = [order[j], order[i]];
      update({ ...content, section_order: order });
    },
    [content],
  );

  if (query.isLoading || !content) return <Spinner label="Loading resume" />;
  if (query.isError) return <Alert tone="error">Could not load this resume.</Alert>;

  const order = content.section_order?.length ? content.section_order : [...SECTIONS];

  function setField<K extends keyof ResumeContent>(key: K, value: ResumeContent[K]) {
    update({ ...content, [key]: value } as ResumeContent);
  }

  return (
    <div>
      <PageHeader
        title={title}
        description={`Updated ${new Date(query.data!.updated_at).toLocaleString()} · origin: ${query.data!.origin}`}
        action={
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-ink-muted" aria-live="polite">
              {saveState === "saving" ? "Saving…" : saveState === "saved" ? "All changes saved" : saveState === "error" ? "Save failed" : ""}
            </span>
            <Link to={`/app/resumes/${resumeId}/analyze`}>
              <Button variant="secondary">
                <Sparkles className="h-4 w-4" aria-hidden /> Analyse
              </Button>
            </Link>
          </div>
        }
      />

      <div className="mb-5 flex flex-wrap items-center gap-2">
        {(["pdf", "docx", "latex", "txt"] as const).map((f) => (
          <Button key={f} variant="secondary" onClick={() => runExport(f)} loading={exporting === f}>
            <Download className="h-4 w-4" aria-hidden /> {f.toUpperCase()}
          </Button>
        ))}
        <Button variant="ghost" onClick={() => duplicate.mutate()} loading={duplicate.isPending}>
          <Copy className="h-4 w-4" aria-hidden /> Duplicate
        </Button>
        <Button
          variant="ghost"
          onClick={() => confirmer() && remove.mutate()}
          loading={remove.isPending}
          className="text-clay-dark"
        >
          <Trash2 className="h-4 w-4" aria-hidden /> Delete
        </Button>
      </div>
      {error && <div className="mb-4"><Alert tone="error">{error}</Alert></div>}

      <div className="grid gap-6 lg:grid-cols-[1.1fr,0.9fr]">
        <div className="space-y-5">
          <Card>
            <h2 className="font-serif text-xl">Details</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="Title" htmlFor="r-title">
                <Input
                  id="r-title"
                  value={title}
                  onChange={(e) => {
                    setTitle(e.target.value);
                    queueSave({ title: e.target.value });
                  }}
                />
              </Field>
              <Field label="Page size" htmlFor="r-page">
                <Select
                  id="r-page"
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(e.target.value);
                    queueSave({ page_size: e.target.value });
                  }}
                >
                  <option value="A4">A4</option>
                  <option value="LETTER">US Letter</option>
                </Select>
              </Field>
            </div>
          </Card>

          <Card>
            <h2 className="font-serif text-xl">Contact</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="Name" htmlFor="c-name">
                <Input id="c-name" value={content.contact.name} onChange={(e) => setField("contact", { ...content.contact, name: e.target.value })} />
              </Field>
              <Field label="Headline" htmlFor="c-head">
                <Input id="c-head" value={content.contact.headline} onChange={(e) => setField("contact", { ...content.contact, headline: e.target.value })} />
              </Field>
              <Field label="Email" htmlFor="c-email">
                <Input id="c-email" value={content.contact.email} onChange={(e) => setField("contact", { ...content.contact, email: e.target.value })} />
              </Field>
              <Field label="Phone" htmlFor="c-phone">
                <Input id="c-phone" value={content.contact.phone} onChange={(e) => setField("contact", { ...content.contact, phone: e.target.value })} />
              </Field>
              <Field label="Location" htmlFor="c-loc">
                <Input id="c-loc" value={content.contact.location} onChange={(e) => setField("contact", { ...content.contact, location: e.target.value })} />
              </Field>
            </div>
            <div className="mt-4">
              <p className="mb-1.5 text-sm font-medium text-ink">Links</p>
              <p className="mb-2 text-xs text-ink-muted">
                Rendered as clickable links labelled by their name (e.g. GitHub, LinkedIn) in exports.
              </p>
              <ContactLinks
                links={content.contact.links ?? []}
                onChange={(links) => setField("contact", { ...content.contact, links })}
              />
            </div>
          </Card>

          {order.map((key, idx) => (
            <Card key={key}>
              <div className="flex items-center justify-between">
                <h2 className="font-serif text-xl capitalize">{key}</h2>
                <div className="flex items-center gap-1">
                  <label className="mr-2 flex items-center gap-1 text-xs text-ink-muted">
                    <input
                      type="checkbox"
                      checked={content.section_visibility?.[key] !== false}
                      onChange={(e) => setField("section_visibility", { ...content.section_visibility, [key]: e.target.checked })}
                    />
                    show
                  </label>
                  <button type="button" className="btn-icon" onClick={() => moveSection(key, -1)} disabled={idx === 0} aria-label={`Move ${key} up`}>
                    <ArrowUp className="h-4 w-4" />
                  </button>
                  <button type="button" className="btn-icon" onClick={() => moveSection(key, 1)} disabled={idx === order.length - 1} aria-label={`Move ${key} down`}>
                    <ArrowDown className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="mt-4">
                {key === "summary" && (
                  <Textarea
                    rows={4}
                    value={content.summary}
                    placeholder="Two or three sentences: what you build and the impact."
                    onChange={(e) => setField("summary", e.target.value)}
                  />
                )}

                {key === "experience" && (
                  <Repeatable
                    items={content.experience}
                    onChange={(items) => setField("experience", items)}
                    blank={(): ExperienceItem => ({ company: "", role: "", location: "", start: "", end: "", bullets: [""] })}
                    render={(item, patch) => (
                      <div className="grid gap-3 sm:grid-cols-2">
                        <Field label="Role"><Input value={item.role} onChange={(e) => patch({ role: e.target.value })} /></Field>
                        <Field label="Company"><Input value={item.company} onChange={(e) => patch({ company: e.target.value })} /></Field>
                        <Field label="Location"><Input value={item.location} onChange={(e) => patch({ location: e.target.value })} /></Field>
                        <div className="grid grid-cols-2 gap-3">
                          <Field label="Start"><Input value={item.start} onChange={(e) => patch({ start: e.target.value })} placeholder="Jun 2024" /></Field>
                          <Field label="End"><Input value={item.end} onChange={(e) => patch({ end: e.target.value })} placeholder="Present" /></Field>
                        </div>
                        <div className="sm:col-span-2">
                          <Bullets bullets={item.bullets} onChange={(bullets) => patch({ bullets })} />
                        </div>
                      </div>
                    )}
                  />
                )}

                {key === "projects" && (
                  <Repeatable
                    items={content.projects}
                    onChange={(items) => setField("projects", items)}
                    blank={(): ProjectItem => ({ name: "", tech: [], link: "", bullets: [""] })}
                    render={(item, patch) => (
                      <div className="grid gap-3 sm:grid-cols-2">
                        <Field label="Name"><Input value={item.name} onChange={(e) => patch({ name: e.target.value })} /></Field>
                        <Field label="Link"><Input value={item.link} onChange={(e) => patch({ link: e.target.value })} /></Field>
                        <div className="sm:col-span-2">
                          <Field label="Tech" hint="Comma-separated">
                            <Input value={item.tech.join(", ")} onChange={(e) => patch({ tech: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} />
                          </Field>
                        </div>
                        <div className="sm:col-span-2">
                          <Bullets bullets={item.bullets} onChange={(bullets) => patch({ bullets })} />
                        </div>
                      </div>
                    )}
                  />
                )}

                {key === "education" && (
                  <Repeatable
                    items={content.education}
                    onChange={(items) => setField("education", items)}
                    blank={(): EducationItem => ({ institution: "", degree: "", location: "", start: "", end: "", details: [""] })}
                    render={(item, patch) => (
                      <div className="grid gap-3 sm:grid-cols-2">
                        <Field label="Institution"><Input value={item.institution} onChange={(e) => patch({ institution: e.target.value })} /></Field>
                        <Field label="Degree"><Input value={item.degree} onChange={(e) => patch({ degree: e.target.value })} /></Field>
                        <div className="grid grid-cols-2 gap-3">
                          <Field label="Start"><Input value={item.start} onChange={(e) => patch({ start: e.target.value })} /></Field>
                          <Field label="End"><Input value={item.end} onChange={(e) => patch({ end: e.target.value })} /></Field>
                        </div>
                        <div className="sm:col-span-2"><Bullets bullets={item.details} onChange={(details) => patch({ details })} /></div>
                      </div>
                    )}
                  />
                )}

                {key === "skills" && (
                  <Repeatable
                    items={content.skills}
                    onChange={(items) => setField("skills", items)}
                    blank={() => ({ category: "Skills", items: [] })}
                    render={(item, patch) => (
                      <div className="grid gap-3 sm:grid-cols-3">
                        <Field label="Category"><Input value={item.category} onChange={(e) => patch({ category: e.target.value })} /></Field>
                        <div className="sm:col-span-2">
                          <Field label="Items" hint="Comma-separated">
                            <Input value={item.items.join(", ")} onChange={(e) => patch({ items: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })} />
                          </Field>
                        </div>
                      </div>
                    )}
                  />
                )}

                {(key === "certifications" || key === "achievements") && (
                  <StringList items={content[key]} onChange={(items) => setField(key, items)} />
                )}
              </div>
            </Card>
          ))}
        </div>

        <div className="lg:sticky lg:top-6 lg:self-start">
          <div className="mb-2 flex items-center justify-between">
            <p className="eyebrow">Live preview</p>
            <Badge tone="neutral">{pageSize === "LETTER" ? "US Letter" : "A4"}</Badge>
          </div>
          <div className="rounded-lg border border-stone-200 bg-stone-100 p-3">
            <ResumePreview content={content} pageSize={pageSize} />
          </div>
          <p className="mt-2 text-xs text-ink-muted">
            Preview reflects the structured data. Exported PDF/DOCX use the same source.
          </p>
        </div>
      </div>
    </div>
  );
}

function confirmer() {
  return window.confirm("Delete this resume and its stored files? This cannot be undone.");
}

function Bullets({ bullets, onChange }: { bullets: string[]; onChange: (b: string[]) => void }) {
  return (
    <div>
      <p className="mb-1.5 text-sm font-medium text-ink">Bullet points</p>
      <div className="space-y-2">
        {bullets.map((b, i) => (
          <div key={i} className="flex items-start gap-2">
            <Textarea
              rows={2}
              value={b}
              placeholder="Action + tool + measurable result (never invent numbers)."
              onChange={(e) => {
                const next = [...bullets];
                next[i] = e.target.value;
                onChange(next);
              }}
            />
            <button type="button" className="btn-icon mt-1" onClick={() => onChange(bullets.filter((_, j) => j !== i))} aria-label="Remove bullet">
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
      <Button variant="ghost" className="mt-2" onClick={() => onChange([...bullets, ""])}>
        <Plus className="h-4 w-4" aria-hidden /> Add bullet
      </Button>
    </div>
  );
}

function ContactLinks({ links, onChange }: { links: LinkItem[]; onChange: (v: LinkItem[]) => void }) {
  function patch(i: number, p: Partial<LinkItem>) {
    onChange(links.map((l, j) => (j === i ? { ...l, ...p } : l)));
  }
  return (
    <div className="space-y-2">
      {links.map((l, i) => (
        <div key={i} className="flex items-center gap-2">
          <Input
            className="max-w-[9.5rem]"
            value={l.label}
            placeholder="Label"
            aria-label={`Link ${i + 1} label`}
            onChange={(e) => patch(i, { label: e.target.value })}
          />
          <Input
            value={l.url}
            placeholder="https://github.com/you"
            aria-label={`Link ${i + 1} URL`}
            onChange={(e) => patch(i, { url: e.target.value })}
          />
          {l.url && ensureUrl(l.url) && (
            <a
              href={ensureUrl(l.url)}
              target="_blank"
              rel="noreferrer noopener"
              className="text-xs text-forest underline decoration-dotted underline-offset-2"
            >
              open
            </a>
          )}
          <button
            type="button"
            className="btn-icon"
            onClick={() => onChange(links.filter((_, j) => j !== i))}
            aria-label="Remove link"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
      <Button variant="ghost" onClick={() => onChange([...links, { label: "", url: "" }])}>
        <Plus className="h-4 w-4" aria-hidden /> Add link
      </Button>
    </div>
  );
}

function StringList({ items, onChange }: { items: string[]; onChange: (v: string[]) => void }) {
  return (
    <div className="space-y-2">
      {items.map((v, i) => (
        <div key={i} className="flex items-center gap-2">
          <Input
            value={v}
            onChange={(e) => {
              const next = [...items];
              next[i] = e.target.value;
              onChange(next);
            }}
          />
          <button type="button" className="btn-icon" onClick={() => onChange(items.filter((_, j) => j !== i))} aria-label="Remove item">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
      <Button variant="ghost" onClick={() => onChange([...items, ""])}>
        <Plus className="h-4 w-4" aria-hidden /> Add item
      </Button>
    </div>
  );
}

function Repeatable<T>({
  items,
  onChange,
  render,
  blank,
}: {
  items: T[];
  onChange: (items: T[]) => void;
  render: (item: T, patch: (p: Partial<T>) => void) => React.ReactNode;
  blank: () => T;
}) {
  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div key={i} className="rounded-md border border-stone-200 bg-ivory-50 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs text-ink-muted">Entry {i + 1}</span>
            <div className="flex gap-1">
              <button type="button" className="btn-icon" disabled={i === 0} onClick={() => move(items, i, -1, onChange)} aria-label="Move up">
                <ArrowUp className="h-3.5 w-3.5" />
              </button>
              <button type="button" className="btn-icon" disabled={i === items.length - 1} onClick={() => move(items, i, 1, onChange)} aria-label="Move down">
                <ArrowDown className="h-3.5 w-3.5" />
              </button>
              <button type="button" className="btn-icon" onClick={() => onChange(items.filter((_, j) => j !== i))} aria-label="Remove entry">
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
          {render(item, (p) => onChange(items.map((it, j) => (j === i ? { ...it, ...p } : it))))}
        </div>
      ))}
      <Button variant="secondary" onClick={() => onChange([...items, blank()])}>
        <Plus className="h-4 w-4" aria-hidden /> Add entry
      </Button>
    </div>
  );
}

function move<T>(items: T[], i: number, dir: -1 | 1, onChange: (items: T[]) => void) {
  const j = i + dir;
  if (j < 0 || j >= items.length) return;
  const next = [...items];
  [next[i], next[j]] = [next[j], next[i]];
  onChange(next);
}
