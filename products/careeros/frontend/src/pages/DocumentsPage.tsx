import { useEffect, useState } from "react";
import * as api from "../api/client";
import { ErrorState, LoadingState, EmptyState } from "../components/StateViews";

export function DocumentsPage() {
  const [documents, setDocuments] = useState<api.DocumentRead[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<unknown>(null);
  // Per-document extraction run state, keyed by document id -- lets
  // each row show its own progress independently.
  const [runs, setRuns] = useState<Record<string, api.DocumentExtractionRunRead>>({});
  const [applySummaries, setApplySummaries] = useState<Record<string, api.ApplySummary>>({});
  const [busyDocId, setBusyDocId] = useState<string | null>(null);

  async function loadDocuments() {
    try {
      const docs = await api.listDocuments();
      setDocuments(docs);
    } catch (err) {
      setError(err);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    setUploading(true);
    try {
      await api.uploadDocument(file);
      await loadDocuments();
    } catch (err) {
      setUploadError(err);
    } finally {
      setUploading(false);
      e.target.value = ""; // allow re-selecting the same file
    }
  }

  async function handleExtract(documentId: string) {
    setBusyDocId(documentId);
    try {
      const run = await api.extractDocument(documentId);
      setRuns((prev) => ({ ...prev, [documentId]: run }));
    } catch (err) {
      setError(err);
    } finally {
      setBusyDocId(null);
    }
  }

  async function handleApply(documentId: string, runId: string) {
    setBusyDocId(documentId);
    try {
      const summary = await api.applyExtractionRun(documentId, runId);
      setApplySummaries((prev) => ({ ...prev, [documentId]: summary }));
    } catch (err) {
      setError(err);
    } finally {
      setBusyDocId(null);
    }
  }

  return (
    <div>
      <h1>CV / Documents</h1>
      <p>Upload your CV (PDF or DOCX) to extract your employment history and skills into Career DNA.</p>

      <div style={{ margin: "1.5rem 0" }}>
        <label>
          <input type="file" accept=".pdf,.docx" onChange={handleFileChange} disabled={uploading} />
        </label>
        {uploading && <LoadingState label="Uploading..." />}
        {uploadError !== null && <ErrorState error={uploadError} />}
      </div>

      {error !== null && <ErrorState error={error} />}
      {documents === null && error === null && <LoadingState label="Loading documents..." />}
      {documents !== null && documents.length === 0 && <EmptyState message="No documents uploaded yet." />}

      {documents !== null && documents.length > 0 && (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {documents.map((doc) => {
            const version = doc.versions[0];
            const run = runs[doc.id];
            const summary = applySummaries[doc.id];
            const busy = busyDocId === doc.id;

            return (
              <li key={doc.id} style={{ border: "1px solid #ddd", borderRadius: 6, padding: "1rem", marginBottom: "1rem" }}>
                <strong>{version?.original_filename ?? "(unknown filename)"}</strong>
                <div style={{ color: "#555", fontSize: "0.9rem" }}>
                  Status: {doc.status} &middot; Type: {doc.document_type.toUpperCase()}
                </div>

                {!run && doc.status === "uploaded" && (
                  <button onClick={() => handleExtract(doc.id)} disabled={busy} style={{ marginTop: "0.5rem", cursor: "pointer" }}>
                    {busy ? "Extracting..." : "Extract"}
                  </button>
                )}

                {run && (
                  <div style={{ marginTop: "0.5rem" }}>
                    <div>
                      Extraction: <strong>{run.status}</strong>
                      {run.overall_confidence !== null && ` (confidence: ${Math.round(run.overall_confidence * 100)}%)`}
                    </div>
                    {run.status === "failed" && run.error_detail && <ErrorState error={run.error_detail} />}
                    {run.status === "completed" && !run.applied_at && !summary && (
                      <button onClick={() => handleApply(doc.id, run.id)} disabled={busy} style={{ marginTop: "0.5rem", cursor: "pointer" }}>
                        {busy ? "Applying..." : "Apply to Career DNA"}
                      </button>
                    )}
                  </div>
                )}

                {summary && (
                  <div style={{ marginTop: "0.5rem", padding: "0.5rem", background: "#f0f7f0", borderRadius: 4 }}>
                    Applied: {summary.employments_applied} employment record(s), {summary.skills_applied} skill(s).
                    <div style={{ fontSize: "0.85rem", color: "#555" }}>{summary.note}</div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
