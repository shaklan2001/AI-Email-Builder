# UI Context

## Theme

Dark-first workspace. Configure via MUI `createTheme` in `frontend/src/theme/muiTheme.ts`.

| MUI token | Usage | Suggested value |
|---|---|---|
| `palette.mode` | Base mode | `dark` |
| `palette.background.default` | Page background | `#0a0a0f` |
| `palette.background.paper` | Cards, panels | `#111118` |
| `palette.primary.main` | Accent, CTAs | `#6366f1` |
| `palette.text.primary` | Body text | `#f0f0f5` |
| `palette.text.secondary` | Muted text | `#7070a0` |
| `palette.error.main` | Errors | `#ef4444` |
| `palette.success.main` | Success | `#22c55e` |
| `palette.warning.main` | Wait steps | `#f59e0b` |

Use `sx` prop and theme tokens — avoid hardcoded hex in components except inside `muiTheme.ts`.

## Typography

- Font: **Inter** or **Roboto** via MUI `typography.fontFamily`
- Body: `variant="body2"` · Headings: `h5`–`h6` · Labels: `caption`

## Component library

**MUI only** (`@mui/material`, `@mui/icons-material`). Do not add shadcn, Chakra, or Tailwind component kits.

| Pattern | MUI components |
|---|---|
| App shell | `AppBar`, `Toolbar`, `Container`, `Box` |
| Campaign list | `Grid`, `Card`, `CardContent`, `Chip` |
| Chat | `Paper`, `List`, `ListItem`, `TextField`, `IconButton` |
| Previews | `Tabs`, `Tab`, `Divider` |
| Upload | `Dialog`, `Button`, `Alert` |
| Analytics | `Grid`, `Card`, `Typography` |
| Loading / errors | `CircularProgress`, `Alert`, `Snackbar` |

## Data fetching

**TanStack Query** — hooks in `frontend/src/api/hooks/`. See `docs/Frontend_Screen_Flow.md` for query keys.

## Layout patterns

- **AI Builder:** ~40% chat (`Paper`) | ~60% preview (`Tabs`: Workflow | Email). `Box` flex row, full viewport height.
- **Dashboard / Analytics:** `Container maxWidth="lg"`, responsive `Grid`.
- **Navbar:** `AppBar` fixed, height 56px, `UserButton` (Clerk) on the right.

## Screen flow

```
/login (Clerk SignIn)
    ↓
/  Dashboard — useWorkflows()
    ↓
/campaigns/new
    ↓
/campaigns/:id/builder — useChat(), previews
    ↓
Recipient upload — useUploadRecipients()
    ↓
/campaigns/:id/review — useActivateWorkflow()
    ↓
/campaigns/:id/analytics — useAnalytics() refetchInterval 30s
```

Full detail: `docs/Frontend_Screen_Flow.md`.

## Workflow preview node accents

| Step type | Visual hint |
|---|---|
| Send email | `primary` border/icon |
| Wait | `warning` |
| Condition | `secondary` or custom violet |
| End | `text.disabled` |

## Icons

`@mui/icons-material` only. Size via `fontSize="small"` / `medium` on `SvgIcon`.
