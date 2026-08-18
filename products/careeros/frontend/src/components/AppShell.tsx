import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function AppShell() {
  const { logout, user } = useAuth();

  const linkStyle = ({ isActive }: { isActive: boolean }) => ({
    marginRight: "1rem",
    fontWeight: isActive ? 700 : 400,
    textDecoration: "none",
    color: isActive ? "#1a1a1a" : "#555",
  });

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 900, margin: "0 auto", padding: "1rem" }}>
      <header style={{ borderBottom: "1px solid #ddd", paddingBottom: "1rem", marginBottom: "1.5rem" }}>
        <nav style={{ display: "flex", alignItems: "center", flexWrap: "wrap" }}>
          <NavLink to="/" end style={linkStyle}>
            Dashboard
          </NavLink>
          <NavLink to="/documents" style={linkStyle}>
            CV / Documents
          </NavLink>
          <NavLink to="/career-dna" style={linkStyle}>
            Career DNA
          </NavLink>
          <NavLink to="/jobs" style={linkStyle}>
            Jobs
          </NavLink>
          <span style={{ flex: 1 }} />
          {user && <span style={{ marginRight: "1rem", color: "#555" }}>{user.email}</span>}
          <button onClick={logout} style={{ cursor: "pointer" }}>
            Logout
          </button>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
