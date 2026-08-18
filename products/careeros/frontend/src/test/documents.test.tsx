import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DocumentsPage } from "../pages/DocumentsPage";
import * as api from "../api/client";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof api>("../api/client");
  return {
    ...actual,
    listDocuments: vi.fn(),
    uploadDocument: vi.fn(),
    extractDocument: vi.fn(),
    applyExtractionRun: vi.fn(),
  };
});

const UPLOADED_DOC: api.DocumentRead = {
  id: "d1", person_id: "p1", document_type: "pdf", status: "uploaded", created_at: "2026-01-01",
  versions: [{ id: "v1", version_number: 1, original_filename: "cv.pdf", mime_type: "application/pdf", size_bytes: 1000, is_current: true, uploaded_at: "2026-01-01" }],
};

beforeEach(() => vi.clearAllMocks());

describe("DocumentsPage", () => {
  it("shows empty state when no documents uploaded yet", async () => {
    vi.mocked(api.listDocuments).mockResolvedValue([]);
    render(<DocumentsPage />);
    await waitFor(() => expect(screen.getByText(/no documents uploaded yet/i)).toBeInTheDocument());
  });

  it("renders an uploaded document with an Extract button", async () => {
    vi.mocked(api.listDocuments).mockResolvedValue([UPLOADED_DOC]);
    render(<DocumentsPage />);
    await waitFor(() => expect(screen.getByText("cv.pdf")).toBeInTheDocument());
    expect(screen.getByText("Extract")).toBeInTheDocument();
  });

  it("CV UPLOAD: selecting a file calls the real upload endpoint and refreshes the list", async () => {
    vi.mocked(api.listDocuments).mockResolvedValueOnce([]).mockResolvedValueOnce([UPLOADED_DOC]);
    vi.mocked(api.uploadDocument).mockResolvedValue(UPLOADED_DOC);
    render(<DocumentsPage />);
    await waitFor(() => screen.getByText(/no documents uploaded yet/i));

    const file = new File(["dummy content"], "cv.pdf", { type: "application/pdf" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(input, file);

    await waitFor(() => expect(api.uploadDocument).toHaveBeenCalledWith(file));
    await waitFor(() => expect(screen.getByText("cv.pdf")).toBeInTheDocument());
  });

  it("EXTRACTION STATUS: clicking Extract calls the real endpoint and shows completed status with confidence", async () => {
    vi.mocked(api.listDocuments).mockResolvedValue([UPLOADED_DOC]);
    vi.mocked(api.extractDocument).mockResolvedValue({
      id: "run1", document_version_id: "v1", provider_name: "deterministic-cv-parser", run_number: 1,
      status: "completed", started_at: "2026-01-01", completed_at: "2026-01-01", overall_confidence: 0.85,
      error_detail: null, applied_at: null, extraction_result: {},
    });
    const user = userEvent.setup();
    render(<DocumentsPage />);
    await waitFor(() => screen.getByText("Extract"));
    await user.click(screen.getByText("Extract"));
    await waitFor(() => expect(screen.getByText(/completed/i)).toBeInTheDocument());
    expect(screen.getByText(/85%/)).toBeInTheDocument();
  });

  it("displays a meaningful error message if extraction fails", async () => {
    vi.mocked(api.listDocuments).mockResolvedValue([UPLOADED_DOC]);
    vi.mocked(api.extractDocument).mockResolvedValue({
      id: "run1", document_version_id: "v1", provider_name: "deterministic-cv-parser", run_number: 1,
      status: "failed", started_at: "2026-01-01", completed_at: "2026-01-01", overall_confidence: null,
      error_detail: "Could not parse PDF structure", applied_at: null, extraction_result: null,
    });
    const user = userEvent.setup();
    render(<DocumentsPage />);
    await waitFor(() => screen.getByText("Extract"));
    await user.click(screen.getByText("Extract"));
    await waitFor(() => expect(screen.getByText(/could not parse pdf structure/i)).toBeInTheDocument());
  });

  it("shows an upload error without crashing the page", async () => {
    vi.mocked(api.listDocuments).mockResolvedValue([]);
    vi.mocked(api.uploadDocument).mockRejectedValue(new api.ApiError(422, { error: { message: "Unsupported file type" } }));
    render(<DocumentsPage />);
    await waitFor(() => screen.getByText(/no documents uploaded yet/i));
    // Named .pdf so it passes the input's accept filter and is
    // actually selected -- the real-world equivalent of this test is
    // a file that passes client-side extension filtering but fails
    // the backend's server-side content-signature validation (see
    // StorageAdapter.validate_upload -- confirmed this session's
    // established backend behaviour, not a hypothetical).
    const file = new File(["not a real pdf"], "corrupt.pdf", { type: "application/pdf" });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(input, file);
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });
});
