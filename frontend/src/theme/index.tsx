import CssBaseline from "@mui/material/CssBaseline";
import {
  createTheme,
  ThemeProvider as MuiThemeProvider,
  type ThemeOptions,
} from "@mui/material/styles";
import merge from "lodash/merge";
import { useMemo } from "react";
import { componentsOverrides } from "./overrides";
import { customShadows } from "./custom-shadows";
import { palette } from "./palette";
import { shadows } from "./shadows";
import { typography } from "./typography";

type Props = {
  children: React.ReactNode;
};

export default function ThemeProvider({ children }: Props) {
  const theme = useMemo(() => {
    const baseOption = {
      palette: palette("light"),
      shadows: shadows("light"),
      customShadows: customShadows("light"),
      typography,
      shape: { borderRadius: 8 },
    };

    const created = createTheme(baseOption as ThemeOptions);
    created.components = merge(componentsOverrides(created));
    return created;
  }, []);

  return (
    <MuiThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </MuiThemeProvider>
  );
}
