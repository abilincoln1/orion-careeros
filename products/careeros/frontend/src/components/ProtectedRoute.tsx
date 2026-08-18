import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LoadingState } from "./StateViews";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) return <LoadingState label="Checking session..." />;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
