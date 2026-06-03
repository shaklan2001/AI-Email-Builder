import { SignIn } from "@clerk/clerk-react";
import Box from "@mui/material/Box";

export function SignInPage() {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 2,
      }}
    >
      <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" />
    </Box>
  );
}
