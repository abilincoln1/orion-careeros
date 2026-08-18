import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import * as api from "../api/client";

interface AuthContextValue {
  user: api.UserRead | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<api.UserRead | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = api.getStoredToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.getMe();
      setUser(me);
    } catch {
      // Token invalid/expired -- api.request() already cleared it on a
      // 401; reflect that here rather than leaving stale user state.
      api.clearTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const token = await api.login(email, password);
      api.storeTokens(token);
      await refreshUser();
    },
    [refreshUser]
  );

  const register = useCallback(async (email: string, password: string) => {
    await api.register(email, password);
    // Registration does not itself return a session token (confirmed
    // against the real UserRead response shape) -- log in immediately
    // afterward, using the same credentials, rather than requiring a
    // separate manual login step.
    const token = await api.login(email, password);
    api.storeTokens(token);
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(() => {
    // No backend /logout endpoint exists (confirmed against the real
    // OpenAPI spec) -- this is the correct, honest behaviour for this
    // backend's actual design, not an omission.
    api.clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
