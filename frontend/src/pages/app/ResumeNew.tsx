import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../../lib/api";
import type { Resume } from "../../lib/types";
import { Alert, Button, Card, Field, Input, Select } from "../../components/ui";
import { PageHeader } from "../../components/Layout";

function blankContent() {
  return {
    contact: { name: "", headline: "", email: "", phone: "", location: "", links: [] },
    summary: "",
    experience: [],
    education: [],
    projects: [],
    skills: [{ category: "Languages", items: [] }],
    certifications: [],
    achievements: [],
    section_order: ["summary", "experience", "projects", "education", "skills", "certifications", "achievements"],
    section_visibility: {},
  };
}

export function ResumeNew() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [title, setTitle] = useState("My Resume");
  const [pageSize, setPageSize] = useState("A4");
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => api.post<Resume>("/resumes", { title, page_size: pageSize, content: blankContent() }),
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ["resumes"] });
      navigate(`/app/resumes/${r.id}`);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create resume."),
  });

  return (
    <div className="mx-auto max-w-lg">
      <PageHeader title="New resume" description="Start from a clean, ATS-friendly single-column template inspired by Jake's Resume." />
      <Card>
        <div className="space-y-4">
          <Field label="Resume title" htmlFor="title">
            <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} />
          </Field>
          <Field label="Page size" hint="A4 is a sensible default for Indian and international applications." htmlFor="ps">
            <Select id="ps" value={pageSize} onChange={(e) => setPageSize(e.target.value)}>
              <option value="A4">A4</option>
              <option value="LETTER">US Letter</option>
            </Select>
          </Field>
          {error && <Alert tone="error">{error}</Alert>}
          <Button loading={create.isPending} onClick={() => create.mutate()} className="w-full">
            Create and edit
          </Button>
        </div>
      </Card>
    </div>
  );
}
