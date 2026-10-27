import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { cn, formatDate, scoreTone } from "../lib/utils";
import { ScoreDial, ScoreBar } from "../components/Score";
import { ResumePreview } from "../components/ResumePreview";
import { Landing } from "../pages/public/Landing";
import type { ResumeContent } from "../lib/types";

const sample: ResumeContent = {
  contact: {
    name: "Asha Rao",
    headline: "Backend-focused CS student",
    email: "asha@example.com",
    phone: "",
    location: "Bengaluru",
    links: [{ label: "GitHub", url: "https://github.com/asha" }],
  },
  summary: "Backend-focused computer science student building REST APIs.",
  experience: [
    { company: "Acme", role: "SWE Intern", location: "Remote", start: "Jun 2024", end: "Aug 2024", bullets: ["Built a REST API in Python", "Wrote unit tests raising coverage"] },
  ],
  education: [{ institution: "IIT", degree: "B.Tech CSE", location: "", start: "2021", end: "2025", details: ["CGPA 9.1"] }],
  projects: [{ name: "Task API", tech: ["FastAPI", "Postgres"], link: "https://github.com/asha/task", bullets: ["Containerised with Docker"] }],
  skills: [{ category: "Languages", items: ["Python", "SQL"] }],
  certifications: ["AWS Cloud Practitioner"],
  achievements: [],
  section_order: ["summary", "experience", "projects", "education", "skills", "certifications", "achievements"],
  section_visibility: {},
};

describe("utils", () => {
  it("cn merges conflicting tailwind classes", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });
  it("formatDate handles empty and valid values", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate("2024-06-01T00:00:00Z")).toContain("2024");
  });
  it("scoreTone buckets scores", () => {
    expect(scoreTone(9)).toContain("forest");
    expect(scoreTone(6)).toContain("ink-soft");
    expect(scoreTone(2)).toContain("clay");
    expect(scoreTone(null)).toContain("muted");
  });
});

describe("Score components", () => {
  it("renders the score value and label", () => {
    render(<ScoreDial value={8} label="Overall" />);
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("Overall")).toBeInTheDocument();
  });
  it("renders dashes when value is null", () => {
    render(<ScoreDial value={null} label="Overall" />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
  it("renders a score bar with label", () => {
    render(<ScoreBar label="impact and action" value={7} />);
    expect(screen.getByText("impact and action")).toBeInTheDocument();
  });
});

describe("ResumePreview", () => {
  it("renders structured resume content", () => {
    render(<ResumePreview content={sample} />);
    expect(screen.getByText("Asha Rao")).toBeInTheDocument();
    expect(screen.getByText(/Built a REST API in Python/)).toBeInTheDocument();
    expect(screen.getByText(/FastAPI, Postgres/)).toBeInTheDocument();
    expect(screen.getByTestId("resume-preview")).toBeInTheDocument();
  });
});

describe("Landing page", () => {
  it("renders hero and interactive demo", () => {
    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
    expect(screen.getByText(/Interactive demo/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Paste a job description/i)).toBeInTheDocument();
  });
});
