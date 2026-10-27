import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { FileText, Upload } from "lucide-react";
import { api, ApiError } from "../../lib/api";
import type { Paged, Resume } from "../../lib/types";
import { Alert, Badge, Button, Card, EmptyState, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { formatDate } from "../../lib/utils";

export function Resumes() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);

  const list = useQuery({ queryKey: ["resumes"], queryFn: () => api.get<Paged<Resume>>("/resumes") });

  const upload = useMutation({
    mutationFn: (file: File) => api.upload<{ resume_id: string; warnings: string[] }>("/resumes/upload", file),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["resumes"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      navigate(`/app/resumes/${res.resume_id}`);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Upload failed."),
  });

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setError(null);
      upload.mutate(file);
    }
    e.target.value = "";
  }

  return (
    <div>
      <PageHeader
        title="Resumes"
        description="Upload any supported format or build one from the template. Originals are preserved."
        action={
          <Link to="/app/resumes/new">
            <Button variant="secondary">Create from template</Button>
          </Link>
        }
      />

      <Card className="mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-medium text-ink">Upload a resume</h2>
            <p className="mt-1 text-sm text-ink-muted">
              PDF, DOCX, DOC, TXT, Markdown, RTF, ODT, LaTeX (TEX), HTML, or a scanned image. Max 10 MB.
            </p>
          </div>
          <Button onClick={() => fileRef.current?.click()} loading={upload.isPending}>
            <Upload className="h-4 w-4" aria-hidden /> Choose file
          </Button>
          <input
            ref={fileRef}
            type="file"
            className="sr-only"
            onChange={onPick}
            accept=".pdf,.docx,.doc,.txt,.md,.markdown,.rtf,.odt,.tex,.latex,.html,.htm,.png,.jpg,.jpeg,.webp"
            aria-label="Resume file"
          />
        </div>
        {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
      </Card>

      {list.isLoading ? (
        <Spinner label="Loading resumes" />
      ) : list.data && list.data.items.length > 0 ? (
        <ul className="grid gap-4 sm:grid-cols-2">
          {list.data.items.map((r) => (
            <li key={r.id}>
              <Link to={`/app/resumes/${r.id}`} className="card flex items-start gap-4 p-5 hover:bg-ivory-50">
                <FileText className="mt-0.5 h-5 w-5 text-forest" aria-hidden />
                <div className="min-w-0">
                  <p className="truncate font-medium text-ink">{r.title}</p>
                  <p className="mt-1 text-xs text-ink-muted">Updated {formatDate(r.updated_at)} · {r.origin}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Badge tone="neutral">{r.page_size}</Badge>
                    {r.latest_version?.source_format && <Badge tone="info">{r.latest_version.source_format}</Badge>}
                    {r.latest_version?.parse_confidence != null && (
                      <Badge tone={r.latest_version.parse_confidence >= 0.7 ? "positive" : "warning"}>
                        confidence {Math.round(r.latest_version.parse_confidence * 100)}%
                      </Badge>
                    )}
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState
          title="No resumes yet"
          description="Upload your current resume to get an explainable quality review, or start from a clean template."
          action={
            <Button onClick={() => fileRef.current?.click()}>
              <Upload className="h-4 w-4" aria-hidden /> Upload a resume
            </Button>
          }
        />
      )}
    </div>
  );
}
