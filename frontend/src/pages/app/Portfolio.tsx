import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ExternalLink, Eye, EyeOff } from "lucide-react";
import { Alert, Badge, Button, Card, EmptyState, Field, Input, SectionHeading, Spinner, Textarea } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { api } from "../../lib/api";
import type { PortfolioPage } from "../../lib/types";

export function Portfolio() {
  const qc = useQueryClient();
  const [page, setPage] = useState<PortfolioPage | null>(null);
  const [bio, setBio] = useState("");
  const [title, setTitle] = useState("");
  const [saved, setSaved] = useState(false);

  const list = useQuery({ queryKey: ["portfolio"], queryFn: () => api.get<PortfolioPage[]>("/portfolio") });

  useEffect(() => {
    if (!page && list.data?.length) {
      setPage(list.data[0]);
      setBio(list.data[0].content?.bio ?? "");
      setTitle(list.data[0].title);
    } else if (!page && list.data && list.data.length === 0) {
      create.mutate();
    }
  }, [list.data, page]);

  const create = useMutation({
    mutationFn: () => api.post<PortfolioPage>("/portfolio"),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["portfolio"] });
      setPage(p);
      setTitle(p.title);
    },
  });

  const update = useMutation({
    mutationFn: (payload: Partial<PortfolioPage> & { content?: Record<string, unknown> }) =>
      api.patch<PortfolioPage>(`/portfolio/${page?.id}`, payload),
    onSuccess: (p) => {
      setPage(p);
      qc.invalidateQueries({ queryKey: ["portfolio"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  if (list.isLoading || create.isPending) return <Spinner label="Loading portfolio" />;
  if (!page) return <EmptyState title="Could not load your portfolio" description="Please refresh and try again." />;

  const publicUrl = `${window.location.origin}/p/${page.slug}`;

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Portfolio"
        description="A single page that showcases only your verified projects and links. Publish when you're ready."
        action={
          <Link to={`/p/${page.slug}`} target="_blank" className="text-sm link-quiet">
            View page <ExternalLink className="inline h-3.5 w-3.5" aria-hidden />
          </Link>
        }
      />

      {saved && <div className="mb-4"><Alert tone="success">Portfolio saved.</Alert></div>}

      <Card className="mb-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {page.published ? <Badge tone="positive">Published</Badge> : <Badge tone="neutral">Draft</Badge>}
            <span className="text-xs text-ink-muted">{publicUrl}</span>
          </div>
          <Button
            variant={page.published ? "secondary" : "primary"}
            onClick={() => update.mutate({ published: !page.published })}
            loading={update.isPending && update.variables?.published !== undefined}
          >
            {page.published ? <><EyeOff className="h-4 w-4" aria-hidden /> Unpublish</> : <><Eye className="h-4 w-4" aria-hidden /> Publish</>}
          </Button>
        </div>
      </Card>

      <Card>
        <SectionHeading title="Page content" />
        <div className="space-y-4">
          <Field label="Title" htmlFor="pf-title">
            <Input id="pf-title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </Field>
          <Field label="Bio" hint="Describe your focus honestly. No invented employers or metrics." htmlFor="pf-bio">
            <Textarea id="pf-bio" rows={4} value={bio} onChange={(e) => setBio(e.target.value)} />
          </Field>
          <div className="space-y-2">
            <p className="text-sm font-medium text-ink-soft">Contact visibility</p>
            {(["show_email", "show_phone"] as const).map((key) => (
              <label key={key} className="flex items-center gap-2 text-sm text-ink-soft">
                <input
                  type="checkbox"
                  checked={Boolean(page.settings?.[key])}
                  onChange={(e) => update.mutate({ settings: { ...page.settings, [key]: e.target.checked } })}
                />
                {key === "show_email" ? "Show email" : "Show phone"}
              </label>
            ))}
          </div>
          <Button onClick={() => update.mutate({ title, content: { ...page.content, bio } })} loading={update.isPending}>
            Save changes
          </Button>
        </div>
      </Card>
    </div>
  );
}
