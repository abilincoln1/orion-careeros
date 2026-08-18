import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { CareerDnaPage } from "../pages/CareerDnaPage";
import * as api from "../api/client";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof api>("../api/client");
  return { ...actual, getMyPerson: vi.fn(), getEmployments: vi.fn(), getPersonSkills: vi.fn() };
});

const PERSON: api.PersonRead = {
  id: "p1", user_id: "u1", first_name: "Abiodun", last_name: "Adeniran",
  preferred_name: null, headline: "Systems Engineer", created_at: "2026-01-01", updated_at: "2026-01-01",
};

const EMPLOYMENT: api.EmploymentRead = {
  id: "e1", person_id: "p1", employer_id: "emp1", employer: { id: "emp1", name: "Wm Morrisons Supermarkets Ltd" },
  role_title_raw: "Technology Analyst - Systems Engineer", employment_type: "full_time",
  start_date: "2022-02-01", end_date: null, is_current: true, description: null, attribution_source: "ai_extracted",
};

const SKILL: api.PersonSkillRead = {
  id: "s1", person_id: "p1", skill_id: "sk1", skill: { id: "sk1", name: "SCCM", skill_type: "technical" },
  proficiency: "intermediate", years_experience: null, attribution_source: "ai_extracted",
};

beforeEach(() => vi.clearAllMocks());

describe("CareerDnaPage", () => {
  it("renders real profile, employment, and skill data from the API", async () => {
    vi.mocked(api.getMyPerson).mockResolvedValue(PERSON);
    vi.mocked(api.getEmployments).mockResolvedValue({ items: [EMPLOYMENT], total: 1 });
    vi.mocked(api.getPersonSkills).mockResolvedValue({ items: [SKILL], total: 1 });

    render(<CareerDnaPage />);
    await waitFor(() => expect(screen.getByText(/Abiodun Adeniran/)).toBeInTheDocument());
    expect(screen.getByText("Technology Analyst - Systems Engineer")).toBeInTheDocument();
    expect(screen.getByText("Wm Morrisons Supermarkets Ltd")).toBeInTheDocument();
    expect(screen.getByText("SCCM")).toBeInTheDocument();
  });

  it("PROVENANCE HONESTY: AI-extracted data is labelled as AI-extracted, not as self-reported", async () => {
    vi.mocked(api.getMyPerson).mockResolvedValue(PERSON);
    vi.mocked(api.getEmployments).mockResolvedValue({ items: [EMPLOYMENT], total: 1 });
    vi.mocked(api.getPersonSkills).mockResolvedValue({ items: [SKILL], total: 1 });

    render(<CareerDnaPage />);
    await waitFor(() => expect(screen.getAllByText(/AI-extracted from your CV/i).length).toBe(2));
    expect(screen.queryByText(/^Self-reported$/)).not.toBeInTheDocument();
  });

  it("shows honest empty states when no employment/skills exist yet", async () => {
    vi.mocked(api.getMyPerson).mockResolvedValue(PERSON);
    vi.mocked(api.getEmployments).mockResolvedValue({ items: [], total: 0 });
    vi.mocked(api.getPersonSkills).mockResolvedValue({ items: [], total: 0 });

    render(<CareerDnaPage />);
    await waitFor(() => expect(screen.getByText(/no employment records yet/i)).toBeInTheDocument());
    expect(screen.getByText(/no skills yet/i)).toBeInTheDocument();
  });

  it("shows an error state on API failure", async () => {
    vi.mocked(api.getMyPerson).mockRejectedValue(new api.ApiError(500, { error: { message: "Server error" } }));
    render(<CareerDnaPage />);
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });
});
