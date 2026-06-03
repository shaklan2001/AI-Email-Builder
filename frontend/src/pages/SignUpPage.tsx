import { SignUp } from "@clerk/clerk-react";
import Box from "@mui/material/Box";

export function SignUpPage() {
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
      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
    </Box>
  );
}
