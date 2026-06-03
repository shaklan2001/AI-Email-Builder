import { useAuth } from "@clerk/clerk-react";
import { Navigate, Outlet } from "react-router-dom";

export function PublicRoute() {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return null;
  }

  if (isSignedIn) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
