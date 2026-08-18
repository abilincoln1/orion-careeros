import { useEffect, useState, type FormEvent } from "react";
import * as api from "../api/client";
import { ApiError } from "../api/client";
import { ErrorState, LoadingState } from "../components/StateViews";

type LoadState = "loading" | "no-profile" | "ready" | "error";

export function DashboardPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [person, setPerson] = useState<api.PersonRead | null>(null);
  const [documentCount, setDocumentCount] = useState<number | null>(null);
  const [employmentCount, setEmploymentCount] = useState<number | null>(null);
  const [skillCount, setSkillCount] = useState<number | null>(null);
  const [jobCount, setJobCount] = useState<number | null>(null);
  const [error, setError] = useState<unknown>(null);

  async function loadDashboard() {
    setState("loading");
    setError(null);
    try {
      const p = await api.getMyPerson();
      setPerson(p);

      // Each of these is independently optional -- a real API failure
      // on one must not blank the whole dashboard, per "display an
      // honest empty/unavailable state rather than inventing it."
      const results = await Promise.allSettled([
        api.listDocuments(),
        api.getEmployments(),
        api.getPersonSkills(),
        api.getJobListings(1, 0), // limit=1 -- only `total` is needed here
      ]);

      setDocumentCount(results[0].status === "fulfilled" ? results[0].value.length : null);
      setEmploymentCount(results[1].status === "fulfilled" ? results[1].value.total : null);
      setSkillCount(results[2].status === "fulfilled" ? results[2].value.total : null);
      setJobCount(results[3].status === "fulfilled" ? results[3].value.total : null);

      setState("ready");
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        // No Person record yet -- a real, expected state for a brand-
        // new user (get_current_person 404s by design), not an error.
        setState("no-profile");
      } else {
        setError(err);
        setState("error");
      }
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (state === "loading") return <LoadingState label="Loading dashboard..." />;
  if (state === "error") return <ErrorState error={error} />;
  if (state === "no-profile") return <CreateProfilePrompt onCreated={loadDashboard} />;

  return (
    <div>
      <h1>Dashboard</h1>
      <p>
        Welcome, {person!.first_name} {person!.last_name}
        {person!.headline ? ` -- ${person!.headline}` : ""}
      </p>
      <dl style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1.5rem" }}>
        <StatCard label="CV / documents uploaded" value={documentCount} />
        <StatCard label="Employment records" value={employmentCount} />
        <StatCard label="Skills" value={skillCount} />
        <StatCard label="Discovered jobs" value={jobCount} />
      </dl>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number | null }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 6, padding: "1rem" }}>
      <dt style={{ color: "#555", fontSize: "0.85rem" }}>{label}</dt>
      {/* value === null means this specific stat's API call failed --
          shown honestly as "unavailable", never silently as 0. */}
      <dd style={{ fontSize: "1.75rem", fontWeight: 700, margin: 0 }}>{value === null ? "unavailable" : value}</dd>
    </div>
  );
}

function CreateProfilePrompt({ onCreated }: { onCreated: () => void }) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.createPerson(firstName, lastName);
      onCreated();
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1>Welcome to CareerOS</h1>
      <p>Let's set up your Career DNA profile to get started.</p>
      {error !== null && <ErrorState error={error} />}
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxWidth: 300 }}>
        <label>
          First name
          <input required value={firstName} onChange={(e) => setFirstName(e.target.value)} style={{ display: "block", width: "100%", padding: "0.5rem" }} />
        </label>
        <label>
          Last name
          <input required value={lastName} onChange={(e) => setLastName(e.target.value)} style={{ display: "block", width: "100%", padding: "0.5rem" }} />
        </label>
        <button type="submit" disabled={submitting} style={{ padding: "0.6rem", cursor: "pointer" }}>
          {submitting ? "Creating..." : "Create profile"}
        </button>
      </form>
    </div>
  );
}
