import { UserButton, useUser } from "@clerk/clerk-react";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { alpha } from "@mui/material/styles";

type Props = {
  collapsed?: boolean;
};

export function NavAccount({ collapsed = false }: Props) {
  const { user } = useUser();

  const displayName =
    user?.fullName ?? user?.username ?? user?.primaryEmailAddress?.emailAddress ?? "Account";
  const email = user?.primaryEmailAddress?.emailAddress ?? "";

  return (
    <Box
      sx={{
        px: collapsed ? 1 : 2,
        py: 2,
        borderTop: (theme) => `dashed 1px ${theme.palette.divider}`,
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        spacing={collapsed ? 0 : 1.5}
        justifyContent={collapsed ? "center" : "flex-start"}
      >
        <UserButton
          appearance={{
            elements: {
              avatarBox: {
                width: collapsed ? 36 : 40,
                height: collapsed ? 36 : 40,
              },
            },
          }}
        />

        {!collapsed && (
          <Box sx={{ minWidth: 0, flex: 1 }}>
            <Typography variant="subtitle2" noWrap>
              {displayName}
            </Typography>
            {email ? (
              <Typography
                variant="caption"
                noWrap
                sx={{ color: "text.secondary", display: "block" }}
              >
                {email}
              </Typography>
            ) : null}
          </Box>
        )}
      </Stack>

      {!collapsed && (
        <Typography
          variant="caption"
          sx={{
            display: "block",
            mt: 1,
            color: (theme) => alpha(theme.palette.text.secondary, 0.8),
          }}
        >
          Manage account via profile menu
        </Typography>
      )}
    </Box>
  );
}
