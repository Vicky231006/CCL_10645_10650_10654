import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import type { Profile } from "../../lib/types";
import { Alert, Button, Card, Field, Input, SectionHeading, Spinner, Textarea } from "../../components/ui";
import { PageHeader } from "../../components/Layout";

export function ProfilePage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["profile"], queryFn: () => api.get<Profile>("/profile") });
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState<Partial<Profile>>({});

  useEffect(() => {
    if (data) setForm(data);
  }, [data]);

  const save = useMutation({
    mutationFn: () =>
      api.patch<Profile>("/profile", {
        headline: form.headline,
        degree: form.degree,
        institution: form.institution,
        graduation_year: form.graduation_year ? Number(form.graduation_year) : null,
        academic_notes: form.academic_notes,
        target_roles: form.target_roles,
        preferred_locations: form.preferred_locations,
        work_arrangement: form.work_arrangement,
        opportunity_type: form.opportunity_type,
        skills: form.skills,
        coursework: form.coursework,
        links: form.links,
        onboarding_completed: true,
      }),
    onSuccess: () => {
      setSaved(true);
      qc.invalidateQueries({ queryKey: ["profile"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      setTimeout(() => setSaved(false), 2500);
    },
  });

  if (isLoading) return <Spinner label="Loading profile" />;

  const list = (v: string[] | undefined) => (v ?? []).join(", ");
  const parseList = (v: string) => v.split(",").map((s) => s.trim()).filter(Boolean);

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title="Profile" description="Keep this current — it powers matching, roadmaps and recommendations." />
      {saved && <div className="mb-4"><Alert tone="success">Profile saved.</Alert></div>}
      <Card>
        <SectionHeading title="Basics" />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Professional headline" htmlFor="headline">
            <Input id="headline" value={form.headline ?? ""} onChange={(e) => setForm({ ...form, headline: e.target.value })} placeholder="Backend-focused CS student" />
          </Field>
          <Field label="Degree" htmlFor="degree">
            <Input id="degree" value={form.degree ?? ""} onChange={(e) => setForm({ ...form, degree: e.target.value })} />
          </Field>
          <Field label="Institution" htmlFor="institution">
            <Input id="institution" value={form.institution ?? ""} onChange={(e) => setForm({ ...form, institution: e.target.value })} />
          </Field>
          <Field label="Graduation year" htmlFor="gy">
            <Input id="gy" type="number" value={form.graduation_year ?? ""} onChange={(e) => setForm({ ...form, graduation_year: e.target.value as unknown as number })} />
          </Field>
        </div>

        <SectionHeading title="Targets" />
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Target roles" hint="Comma-separated" htmlFor="tr">
            <Input id="tr" value={list(form.target_roles)} onChange={(e) => setForm({ ...form, target_roles: parseList(e.target.value) })} />
          </Field>
          <Field label="Preferred locations" hint="Comma-separated" htmlFor="pl">
            <Input id="pl" value={list(form.preferred_locations)} onChange={(e) => setForm({ ...form, preferred_locations: parseList(e.target.value) })} />
          </Field>
          <Field label="Skills" hint="Comma-separated" htmlFor="sk">
            <Input id="sk" value={list(form.skills)} onChange={(e) => setForm({ ...form, skills: parseList(e.target.value) })} />
          </Field>
          <Field label="Relevant coursework" hint="Comma-separated" htmlFor="cw">
            <Input id="cw" value={list(form.coursework)} onChange={(e) => setForm({ ...form, coursework: parseList(e.target.value) })} />
          </Field>
        </div>

        <SectionHeading title="Links" />
        <div className="grid gap-4 sm:grid-cols-3">
          {(["github", "linkedin", "portfolio"] as const).map((key) => (
            <Field key={key} label={key[0].toUpperCase() + key.slice(1)} htmlFor={`link-${key}`}>
              <Input
                id={`link-${key}`}
                value={(form.links?.[key] as string) ?? ""}
                onChange={(e) => setForm({ ...form, links: { ...(form.links ?? {}), [key]: e.target.value } })}
                placeholder="https://"
              />
            </Field>
          ))}
        </div>

        <SectionHeading title="Notes" />
        <Field label="Academic notes" htmlFor="an">
          <Textarea id="an" rows={3} value={form.academic_notes ?? ""} onChange={(e) => setForm({ ...form, academic_notes: e.target.value })} />
        </Field>

        <div className="mt-6">
          <Button loading={save.isPending} onClick={() => save.mutate()}>
            Save profile
          </Button>
        </div>
      </Card>
    </div>
  );
}
