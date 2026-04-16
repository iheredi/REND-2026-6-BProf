import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { ReactNode } from "react";

interface ProtectedProps {
  children: ReactNode;
}

export default function Protected({ children }: ProtectedProps) {
  const { user, loading } = useAuth();

  // amíg validáljuk a /me-t
  if (loading) {
    return <div>Loading...</div>;
  }
  // ha nincs user, login
  if (user === null) {
    return <Navigate to="/login" replace />;
  }

  return children;
}