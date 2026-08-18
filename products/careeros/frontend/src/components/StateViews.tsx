import { ApiError } from "../api/client";

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div role="status" style={{ padding: "1rem", color: "#555" }}>
      {label}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div role="status" style={{ padding: "1rem", color: "#555", fontStyle: "italic" }}>
      {message}
    </div>
  );
}

export function ErrorState({ error }: { error: unknown }) {
  const message = error instanceof ApiError ? error.message : error instanceof Error ? error.message : String(error);
  return (
    <div role="alert" style={{ padding: "1rem", color: "#b00020", background: "#fde8e8", borderRadius: 4 }}>
      Error: {message}
    </div>
  );
}
