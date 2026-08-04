import { useEffect, useState } from "react";
import { fetchHealth, type HealthStatus } from "./api/client";

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch((e) => setError(String(e)));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem", maxWidth: 640 }}>
      <h1>CareerOS -- Project ORION</h1>
      <p>Sprint 1: engineering foundation.</p>
      <h2>Backend status</h2>
      {error && <p style={{ color: "crimson" }}>Error: {error}</p>}
      {!error && !health && <p>Checking backend health...</p>}
      {health && (
        <ul>
          <li>Status: {health.status}</li>
          <li>Service: {health.service}</li>
          <li>Version: {health.version}</li>
          <li>Environment: {health.environment}</li>
        </ul>
      )}
    </main>
  );
}
