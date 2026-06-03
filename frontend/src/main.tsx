import { ClerkProvider } from "@clerk/clerk-react";
import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { QueryProvider } from "./providers/QueryProvider";
import { muiTheme } from "./theme/muiTheme";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!publishableKey) {
  throw new Error("Missing VITE_CLERK_PUBLISHABLE_KEY");
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ClerkProvider
      publishableKey={publishableKey}
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      afterSignInUrl="/dashboard"
      afterSignUpUrl="/dashboard"
      afterSignOutUrl="/sign-in"
    >
      <QueryProvider>
        <ThemeProvider theme={muiTheme}>
          <CssBaseline />
          <App />
        </ThemeProvider>
      </QueryProvider>
    </ClerkProvider>
  </StrictMode>,
);
