/**
 * Typed API client for CareerOS. Every interface below was generated
 * by reading the real, running backend's OpenAPI schema directly
 * (products/careeros/backend, `app.openapi()`), not assumed or guessed
 * -- per the UI MVP directive's explicit "do not assume endpoint
 * names... do not invent APIs" instruction (Section 10).
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8010/api/v1";

// ---------------------------------------------------------------------
// Shared error type
// ---------------------------------------------------------------------

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    // Prefer the backend's own message text where present, per the
    // directive's "display meaningful error messages returned by the
    // backend" instruction -- never a generic string that hides what
    // the backend actually said.
    const message =
      typeof detail === "object" && detail !== null && "error" in detail
        ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (detail as any).error?.message ?? JSON.stringify(detail)
        : JSON.stringify(detail);
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

// ---------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserRead {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

// ---------------------------------------------------------------------
// Career DNA
// ---------------------------------------------------------------------

export interface PersonRead {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  preferred_name: string | null;
  headline: string | null;
  created_at: string;
  updated_at: string;
}

export interface CareerProfileRead {
  id: string;
  person_id: string;
  summary: string | null;
  career_stage: string | null;
  total_experience_months: number | null;
}

export interface EmployerRead {
  id: string;
  name: string;
}

export type AttributionSource = "self_reported" | "inferred" | "verified" | "ai_extracted" | "imported";

export interface EmploymentRead {
  id: string;
  person_id: string;
  employer_id: string;
  employer: EmployerRead | null;
  role_title_raw: string;
  employment_type: string;
  start_date: string;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
  attribution_source: AttributionSource;
}

export interface SkillRead {
  id: string;
  name: string;
  skill_type: string;
}

export interface PersonSkillRead {
  id: string;
  person_id: string;
  skill_id: string;
  skill: SkillRead | null;
  proficiency: string;
  years_experience: number | null;
  attribution_source: AttributionSource;
}

// ---------------------------------------------------------------------
// Document Intelligence
// ---------------------------------------------------------------------

export type DocumentType = "pdf" | "docx";
export type DocumentStatus = "uploaded" | "extracted" | "validated" | "imported" | "archived";
export type DocumentExtractionRunStatus = "pending" | "completed" | "failed";

export interface DocumentVersionRead {
  id: string;
  version_number: number;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  is_current: boolean;
  uploaded_at: string;
}

export interface DocumentRead {
  id: string;
  person_id: string;
  document_type: DocumentType;
  status: DocumentStatus;
  created_at: string;
  versions: DocumentVersionRead[];
}

export interface DocumentExtractionRunRead {
  id: string;
  document_version_id: string;
  provider_name: string;
  run_number: number;
  status: DocumentExtractionRunStatus;
  started_at: string;
  completed_at: string | null;
  overall_confidence: number | null;
  error_detail: string | null;
  applied_at: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  extraction_result: any;
}

export interface ApplySummary {
  person_updated: boolean;
  employments_applied: number;
  employments_skipped_conflict: number;
  skills_applied: number;
  skills_skipped_duplicate: number;
  note: string;
}

// ---------------------------------------------------------------------
// Job Discovery
// ---------------------------------------------------------------------

export interface DiscoveryRequest {
  location?: string | null;
  remote_only?: boolean | null;
  salary_min?: number | null;
  salary_max?: number | null;
}

export interface DiscoveryResponse {
  provider_name: string;
  query_used: string;
  listings_found: number;
  listings_new: number;
  listings_duplicate: number;
}

export interface JobListingRead {
  id: string;
  title: string;
  company_name_raw: string;
  location_raw: string | null;
  is_remote: boolean;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  salary_disclosed: boolean;
  description_raw: string | null;
  source_url: string;
  posted_at: string | null;
  discovered_at: string;
}

export interface JobListingPage {
  items: JobListingRead[];
  total: number;
  limit: number;
  offset: number;
}

// ---------------------------------------------------------------------
// Token storage -- localStorage, matching this backend's bearer-token
// design exactly (no cookie/session mechanism exists to build around).
// ---------------------------------------------------------------------

const TOKEN_KEY = "careeros_access_token";
const REFRESH_KEY = "careeros_refresh_token";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function storeTokens(token: Token): void {
  localStorage.setItem(TOKEN_KEY, token.access_token);
  localStorage.setItem(REFRESH_KEY, token.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// ---------------------------------------------------------------------
// Core request helper
// ---------------------------------------------------------------------

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; isForm?: boolean; auth?: boolean } = {}
): Promise<T> {
  const { method = "GET", body, isForm = false, auth = true } = options;
  const headers: Record<string, string> = {};

  if (auth) {
    const token = getStoredToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let requestBody: BodyInit | undefined;
  if (body !== undefined) {
    if (isForm) {
      requestBody = body as FormData;
      // Do not set Content-Type -- the browser sets the correct
      // multipart boundary automatically; setting it manually breaks
      // multipart uploads.
    } else {
      headers["Content-Type"] = "application/json";
      requestBody = JSON.stringify(body);
    }
  }

  const res = await fetch(`${API_BASE_URL}${path}`, { method, headers, body: requestBody });

  if (res.status === 401 && auth) {
    // Token invalid/expired -- clear it so AuthProvider's next render
    // reflects "logged out" rather than silently retrying forever.
    clearTokens();
  }

  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = { error: { message: res.statusText } };
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ---------------------------------------------------------------------
// Auth endpoints
// ---------------------------------------------------------------------

export function register(email: string, password: string): Promise<UserRead> {
  return request<UserRead>("/auth/register", { method: "POST", body: { email, password }, auth: false });
}

export function login(email: string, password: string): Promise<Token> {
  return request<Token>("/auth/login", { method: "POST", body: { email, password }, auth: false });
}

export function getMe(): Promise<UserRead> {
  return request<UserRead>("/auth/me");
}

// ---------------------------------------------------------------------
// Career DNA endpoints
// ---------------------------------------------------------------------

export function createPerson(firstName: string, lastName: string): Promise<PersonRead> {
  return request<PersonRead>("/career-dna/person", {
    method: "POST",
    body: { first_name: firstName, last_name: lastName },
  });
}

export function getMyPerson(): Promise<PersonRead> {
  return request<PersonRead>("/career-dna/person/me");
}

export function getMyCareerProfile(): Promise<CareerProfileRead> {
  return request<CareerProfileRead>("/career-dna/person/me/profile");
}

export function getEmployments(): Promise<{ items: EmploymentRead[]; total: number }> {
  return request("/career-dna/employments");
}

export function getPersonSkills(): Promise<{ items: PersonSkillRead[]; total: number }> {
  return request("/career-dna/person-skills");
}

// ---------------------------------------------------------------------
// Document Intelligence endpoints
// ---------------------------------------------------------------------

export function listDocuments(): Promise<DocumentRead[]> {
  return request<DocumentRead[]>("/document-intelligence/documents");
}

export function uploadDocument(file: File): Promise<DocumentRead> {
  const form = new FormData();
  form.append("file", file);
  return request<DocumentRead>("/document-intelligence/documents", { method: "POST", body: form, isForm: true });
}

export function extractDocument(documentId: string): Promise<DocumentExtractionRunRead> {
  return request<DocumentExtractionRunRead>(`/document-intelligence/documents/${documentId}/extract`, {
    method: "POST",
  });
}

export function getExtractionRun(documentId: string, runId: string): Promise<DocumentExtractionRunRead> {
  return request<DocumentExtractionRunRead>(`/document-intelligence/documents/${documentId}/runs/${runId}`);
}

export function applyExtractionRun(documentId: string, runId: string): Promise<ApplySummary> {
  return request<ApplySummary>(`/document-intelligence/documents/${documentId}/runs/${runId}/apply`, {
    method: "POST",
  });
}

// ---------------------------------------------------------------------
// Job Discovery endpoints
// ---------------------------------------------------------------------

export function discoverJobs(req: DiscoveryRequest = {}): Promise<DiscoveryResponse> {
  return request<DiscoveryResponse>("/job-discovery/discover", { method: "POST", body: req });
}

export function getJobListings(limit = 50, offset = 0): Promise<JobListingPage> {
  return request<JobListingPage>(`/job-discovery/listings?limit=${limit}&offset=${offset}`);
}

// ---------------------------------------------------------------------
// Health (retained from Sprint 1 scaffold)
// ---------------------------------------------------------------------

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export function fetchHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/health", { auth: false });
}
