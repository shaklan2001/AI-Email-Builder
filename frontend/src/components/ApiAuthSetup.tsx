import { useAuth } from "@clerk/clerk-react";
import { useEffect } from "react";
import { setAuthTokenGetter } from "../api/client";

export function ApiAuthSetup() {
  const { getToken } = useAuth();

  useEffect(() => {
    setAuthTokenGetter(() => getToken());
  }, [getToken]);

  return null;
}
