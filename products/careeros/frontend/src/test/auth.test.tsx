import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { AuthProvider, useAuth } from "../auth/AuthContext";
import { ProtectedRoute } from "../components/ProtectedRoute";
import * as api from "../api/client";

vi.mock("../api/client", async () => {
  const actual = await vi.importActual<typeof api>("../api/client");
  return {
    ...actual,
    getMe: vi.fn(),
    login: vi.fn(),
    register: vi.fn(),
  };
});

function TestConsumer() {
  const { user, loading } = useAuth();
  if (loading) return <div>loading</div>;
  return <div>{user ? `logged in as ${user.email}` : "logged out"}</div>;
}

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
});

describe("AuthProvider", () => {
  it("reflects logged-out state when no token is stored", async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByText("logged out")).toBeInTheDocument());
  });

  it("reflects logged-in state when a valid token exists and /auth/me succeeds", async () => {
    localStorage.setItem("careeros_access_token", "fake-token");
    vi.mocked(api.getMe).mockResolvedValue({
      id: "1", email: "test@example.com", full_name: null, is_active: true, is_superuser: false, created_at: "2026-01-01",
    });
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByText("logged in as test@example.com")).toBeInTheDocument());
  });

  it("clears token and reflects logged-out state when /auth/me returns 401", async () => {
    localStorage.setItem("careeros_access_token", "expired-token");
    vi.mocked(api.getMe).mockRejectedValue(new api.ApiError(401, { error: { message: "Could not validate credentials" } }));
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByText("logged out")).toBeInTheDocument());
    expect(localStorage.getItem("careeros_access_token")).toBeNull();
  });
});

describe("ProtectedRoute", () => {
  it("redirects to /login when not authenticated", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div>login page</div>} />
            <Route path="/" element={<ProtectedRoute><div>secret dashboard</div></ProtectedRoute>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText("login page")).toBeInTheDocument());
    expect(screen.queryByText("secret dashboard")).not.toBeInTheDocument();
  });

  it("renders protected content when authenticated", async () => {
    localStorage.setItem("careeros_access_token", "valid-token");
    vi.mocked(api.getMe).mockResolvedValue({
      id: "1", email: "test@example.com", full_name: null, is_active: true, is_superuser: false, created_at: "2026-01-01",
    });
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<div>login page</div>} />
            <Route path="/" element={<ProtectedRoute><div>secret dashboard</div></ProtectedRoute>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText("secret dashboard")).toBeInTheDocument());
  });
});

describe("LoginPage-level login flow", () => {
  it("stores tokens and updates auth state on successful login", async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: "tok", refresh_token: "ref", token_type: "bearer" });
    vi.mocked(api.getMe).mockResolvedValue({
      id: "1", email: "test@example.com", full_name: null, is_active: true, is_superuser: false, created_at: "2026-01-01",
    });

    function LoginTrigger() {
      const { login, user } = useAuth();
      return (
        <div>
          <button onClick={() => login("test@example.com", "supersecret1")}>do login</button>
          {user && <div>logged in as {user.email}</div>}
        </div>
      );
    }

    const user = userEvent.setup();
    render(
      <AuthProvider>
        <LoginTrigger />
      </AuthProvider>
    );
    await user.click(screen.getByText("do login"));
    await waitFor(() => expect(screen.getByText("logged in as test@example.com")).toBeInTheDocument());
    expect(localStorage.getItem("careeros_access_token")).toBe("tok");
  });
});
