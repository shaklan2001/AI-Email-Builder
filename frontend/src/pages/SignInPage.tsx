import { SignIn } from "@clerk/clerk-react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Logo from "src/components/logo";

export function SignInPage() {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 2,
        bgcolor: "background.neutral",
      }}
    >
      <Stack spacing={3} alignItems="center">
        <Logo disabledLink sx={{ width: 80, height: 80 }} />
        <Typography variant="h4">Welcome back</Typography>
        <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" />
      </Stack>
    </Box>
  );
}
