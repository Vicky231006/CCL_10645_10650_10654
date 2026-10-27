import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../lib/api";
import { Alert, Button, Card, Field, Input, Select } from "../../components/ui";
import { PageHeader } from "../../components/Layout";

export function Onboarding() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    degree: "",
    institution: "",
    graduation_year: "" as string | number,
    target_roles: "",
    preferred_locations: "",
    work_arrangement: "any",
    opportunity_type: "either",
    skills: "",
    links: { github: "", linkedin: "", portfolio: "" } as Record<string, string>,
  });

  const save = useMutation({
    mutationFn: (completed: boolean) =>
      api.patch("/profile", {
        degree: form.degree || null,
        institution: form.institution || null,
        graduation_year: form.graduation_year ? Number(form.graduation_year) : null,
        target_roles: form.target_roles ? form.target_roles.split(",").map((s) => s.trim()).filter(Boolean) : [],
        preferred_locations: form.preferred_locations ? form.preferred_locations.split(",").map((s) => s.trim()).filter(Boolean) : [],
        work_arrangement: form.work_arrangement,
        opportunity_type: form.opportunity_type,
        skills: form.skills ? form.skills.split(",").map((s) => s.trim()).filter(Boolean) : [],
        links: Object.fromEntries(Object.entries(form.links).filter(([, v]) => v)),
        onboarding_completed: completed,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["profile"] });
      navigate("/app");
    },
    onError: () => setError("Could not save your profile. Please try again."),
  });

  const steps = [
    {
      title: "Your studies",
      body: (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Degree" htmlFor="degree">
            <Input id="degree" value={form.degree} onChange={(e) => setForm({ ...form, degree: e.target.value })} placeholder="B.Tech Computer Science" />
          </Field>
          <Field label="Institution" htmlFor="institution">
            <Input id="institution" value={form.institution} onChange={(e) => setForm({ ...form, institution: e.target.value })} />
          </Field>
          <Field label="Graduation year" htmlFor="grad">
            <Input id="grad" type="number" value={form.graduation_year} onChange={(e) => setForm({ ...form, graduation_year: e.target.value })} />
          </Field>
        </div>
      ),
    },
    {
      title: "What you're aiming for",
      body: (
        <div className="grid gap-4">
          <Field label="Target roles" hint="Comma-separated, e.g. Backend Intern, SWE Intern" htmlFor="roles">
            <Input id="roles" value={form.target_roles} onChange={(e) => setForm({ ...form, target_roles: e.target.value })} />
          </Field>
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="Locations" htmlFor="loc">
              <Input id="loc" value={form.preferred_locations} onChange={(e) => setForm({ ...form, preferred_locations: e.target.value })} placeholder="Bengaluru, Remote" />
            </Field>
            <Field label="Work arrangement" htmlFor="wa">
              <Select id="wa" value={form.work_arrangement} onChange={(e) => setForm({ ...form, work_arrangement: e.target.value })}>
                <option value="any">Any</option>
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite">On-site</option>
              </Select>
            </Field>
            <Field label="Opportunity" htmlFor="ot">
              <Select id="ot" value={form.opportunity_type} onChange={(e) => setForm({ ...form, opportunity_type: e.target.value })}>
                <option value="either">Either</option>
                <option value="internship">Internship</option>
                <option value="full_time">Full-time</option>
              </Select>
            </Field>
          </div>
        </div>
      ),
    },
    {
      title: "Skills and links",
      body: (
        <div className="grid gap-4">
          <Field label="Skills" hint="Comma-separated" htmlFor="skills">
            <Input id="skills" value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} placeholder="Python, React, SQL" />
          </Field>
          <div className="grid gap-4 sm:grid-cols-3">
            {(["github", "linkedin", "portfolio"] as const).map((key) => (
              <Field key={key} label={key[0].toUpperCase() + key.slice(1)} htmlFor={key}>
                <Input
                  id={key}
                  value={form.links[key]}
                  onChange={(e) => setForm({ ...form, links: { ...form.links, [key]: e.target.value } })}
                  placeholder="https://"
                />
              </Field>
            ))}
          </div>
        </div>
      ),
    },
  ];

  const isLast = step === steps.length - 1;

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Set up your profile" description="This personalises job discovery, gap analysis and roadmaps. You can skip and add details later." />
      <div className="mb-4 flex gap-2" aria-label="Onboarding progress">
        {steps.map((s, i) => (
          <div key={s.title} className={`h-1.5 flex-1 rounded-full ${i <= step ? "bg-forest" : "bg-stone-200"}`} />
        ))}
      </div>
      <Card>
        <h2 className="font-serif text-xl">{steps[step].title}</h2>
        <div className="mt-4">{steps[step].body}</div>
        {error && <div className="mt-4"><Alert tone="error">{error}</Alert></div>}
        <div className="mt-6 flex items-center justify-between">
          <Button variant="ghost" onClick={() => (step === 0 ? navigate("/app") : setStep(step - 1))}>
            {step === 0 ? "Skip for now" : "Back"}
          </Button>
          <div className="flex gap-2">
            {!isLast && (
              <Button variant="secondary" onClick={() => setStep(step + 1)}>
                Next
              </Button>
            )}
            <Button loading={save.isPending} onClick={() => (isLast ? save.mutate(true) : setStep(step + 1))}>
              {isLast ? "Finish setup" : "Continue"}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
