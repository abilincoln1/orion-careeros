/**
 * Minimal typed API client. Sprint 1 exposes only the health endpoint
 * consumption; auth-aware requests (Authorization header, token refresh)
 * are added alongside the Application Studio / Dashboard sprints.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status}`);
  }
  return res.json();
}
