import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ErrorState } from "../components/StateViews";

export function LoginPage() {
  const { user, login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
    } catch (err) {
      setError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "4rem auto", fontFamily: "system-ui, sans-serif" }}>
      <h1>CareerOS</h1>
      <h2>{mode === "login" ? "Log in" : "Register"}</h2>
      {error !== null && <ErrorState error={error} />}
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <label>
          Email
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ display: "block", width: "100%", padding: "0.5rem" }}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ display: "block", width: "100%", padding: "0.5rem" }}
          />
        </label>
        <button type="submit" disabled={submitting} style={{ padding: "0.6rem", cursor: "pointer" }}>
          {submitting ? "Please wait..." : mode === "login" ? "Log in" : "Register"}
        </button>
      </form>
      <p style={{ marginTop: "1rem" }}>
        {mode === "login" ? (
          <>
            No account?{" "}
            <button onClick={() => setMode("register")} style={{ cursor: "pointer" }}>
              Register
            </button>
          </>
        ) : (
          <>
            Already have an account?{" "}
            <button onClick={() => setMode("login")} style={{ cursor: "pointer" }}>
              Log in
            </button>
          </>
        )}
      </p>
    </div>
  );
}
