import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../../lib/auth";
import { api } from "../../lib/api";
import type { AiStatus } from "../../lib/types";
import { Badge, Button, Card, SectionHeading, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/Layout";
import { formatDate } from "../../lib/utils";

interface FormatInfo {
  formats: string[];
  max_upload_mb: number;
}

export function SettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const ai = useQuery({ queryKey: ["ai-status"], queryFn: () => api.get<AiStatus>("/meta/ai-status") });
  const formats = useQuery({ queryKey: ["formats"], queryFn: () => api.get<FormatInfo>("/meta/formats") });

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Settings" description="Account, AI configuration, and data controls." />

      <Card className="mb-6">
        <SectionHeading title="Account" />
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between"><dt className="text-ink-muted">Email</dt><dd className="text-ink">{user?.email}</dd></div>
          <div className="flex justify-between"><dt className="text-ink-muted">Name</dt><dd className="text-ink">{user?.full_name ?? "—"}</dd></div>
          <div className="flex justify-between"><dt className="text-ink-muted">Member since</dt><dd className="text-ink">{user ? formatDate(user.created_at) : "—"}</dd></div>
        </dl>
        <div className="mt-4">
          <Button variant="secondary" onClick={handleLogout}>Sign out</Button>
        </div>
      </Card>

      <Card className="mb-6">
        <SectionHeading title="AI provider" description="AI features are optional. Deterministic parsing, scoring, matching and export never require it." />
        {ai.isLoading ? (
          <Spinner label="Checking provider" />
        ) : ai.data ? (
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-ink-muted">Configured</span>
              <span className="text-ink">{ai.data.configured}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-ink-muted">Model</span>
              <span className="text-ink">{ai.data.model || "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-ink-muted">Reachable</span>
              <Badge tone={ai.data.available ? "positive" : "warning"}>{ai.data.available ? "yes" : "no"}</Badge>
            </div>
            <p className="text-xs text-ink-muted">{ai.data.detail}</p>
          </div>
        ) : null}
      </Card>

      <Card className="mb-6">
        <SectionHeading title="Supported upload formats" />
        {formats.isLoading ? (
          <Spinner label="Loading formats" />
        ) : (
          <>
            <div className="flex flex-wrap gap-1.5">
              {formats.data?.formats.map((f) => <Badge key={f} tone="neutral">{f}</Badge>)}
            </div>
            <p className="mt-3 text-xs text-ink-muted">Maximum upload size: {formats.data?.max_upload_mb ?? "—"} MB.</p>
          </>
        )}
      </Card>

      <Card className="border-clay/30">
        <SectionHeading title="Data controls" description="You own your data. Delete individual resumes from their editor; deleting a resume also removes its stored files." />
        <p className="text-sm text-ink-muted">
          For full account deletion in this demonstration deployment, contact the operator. Resumo never uses your
          documents to train models without your informed consent.
        </p>
      </Card>
    </div>
  );
}
