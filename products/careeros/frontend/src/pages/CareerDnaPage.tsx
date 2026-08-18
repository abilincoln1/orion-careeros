import { useEffect, useState } from "react";
import * as api from "../api/client";
import { ErrorState, LoadingState, EmptyState } from "../components/StateViews";

const PROVENANCE_LABELS: Record<api.AttributionSource, string> = {
  self_reported: "Self-reported",
  ai_extracted: "AI-extracted from your CV",
  verified: "Verified (evidence-linked)",
  inferred: "Inferred",
  imported: "Imported",
};

function ProvenanceBadge({ source }: { source: api.AttributionSource }) {
  // Backend is the sole authority for this value -- this component
  // only renders the label the API already returned, per the
  // directive's "do not create frontend-specific provenance logic"
  // instruction. AI-extracted data is never rendered as if the
  // candidate personally typed it.
  return (
    <span
      style={{
        fontSize: "0.75rem",
        padding: "0.15rem 0.5rem",
        borderRadius: 12,
        background: source === "ai_extracted" ? "#e3f2fd" : "#f0f0f0",
        color: "#333",
        marginLeft: "0.5rem",
      }}
    >
      {PROVENANCE_LABELS[source]}
    </span>
  );
}

export function CareerDnaPage() {
  const [person, setPerson] = useState<api.PersonRead | null>(null);
  const [employments, setEmployments] = useState<api.EmploymentRead[] | null>(null);
  const [skills, setSkills] = useState<api.PersonSkillRead[] | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    (async () => {
      try {
        const [p, emps, sks] = await Promise.all([api.getMyPerson(), api.getEmployments(), api.getPersonSkills()]);
        setPerson(p);
        setEmployments(emps.items);
        setSkills(sks.items);
      } catch (err) {
        setError(err);
      }
    })();
  }, []);

  if (error !== null) return <ErrorState error={error} />;
  if (person === null) return <LoadingState label="Loading Career DNA..." />;

  return (
    <div>
      <h1>Career DNA</h1>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Profile</h2>
        <p>
          {person.first_name} {person.last_name}
          {person.headline && <><br />{person.headline}</>}
        </p>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h2>Employment</h2>
        {employments === null && <LoadingState />}
        {employments !== null && employments.length === 0 && (
          <EmptyState message="No employment records yet. Upload a CV to extract your work history." />
        )}
        {employments !== null && employments.length > 0 && (
          <ul style={{ listStyle: "none", padding: 0 }}>
            {employments.map((emp) => (
              <li key={emp.id} style={{ border: "1px solid #ddd", borderRadius: 6, padding: "0.75rem", marginBottom: "0.5rem" }}>
                <strong>{emp.role_title_raw}</strong>
                <ProvenanceBadge source={emp.attribution_source} />
                <div style={{ color: "#555" }}>{emp.employer?.name ?? "Unknown employer"}</div>
                <div style={{ fontSize: "0.85rem", color: "#777" }}>
                  {emp.start_date} &ndash; {emp.is_current ? "Present" : emp.end_date ?? "unknown"}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Skills</h2>
        {skills === null && <LoadingState />}
        {skills !== null && skills.length === 0 && (
          <EmptyState message="No skills yet. Upload a CV to extract your skills." />
        )}
        {skills !== null && skills.length > 0 && (
          <ul style={{ listStyle: "none", padding: 0, display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
            {skills.map((s) => (
              <li key={s.id} style={{ border: "1px solid #ddd", borderRadius: 6, padding: "0.4rem 0.75rem" }}>
                {s.skill?.name ?? "Unknown skill"}
                <ProvenanceBadge source={s.attribution_source} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
