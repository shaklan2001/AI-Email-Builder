import { createTheme } from "@mui/material/styles";

export const muiTheme = createTheme({
  palette: {
    mode: "dark",
    background: {
      default: "#0a0a0f",
      paper: "#111118",
    },
    primary: { main: "#6366f1" },
    text: {
      primary: "#f0f0f5",
      secondary: "#7070a0",
    },
  },
});
