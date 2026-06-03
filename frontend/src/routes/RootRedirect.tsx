import { useAuth } from "@clerk/clerk-react";
import { Navigate } from "react-router-dom";

export function RootRedirect() {
  const { isLoaded, isSignedIn } = useAuth();

  if (!isLoaded) {
    return null;
  }

  return <Navigate to={isSignedIn ? "/dashboard" : "/sign-in"} replace />;
}
