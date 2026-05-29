Clerk is already installed and configured.

Wire Clerk into the application and protect all application routes.

## Design

Authentication should feel invisible.

Unauthenticated users should never see application pages.

Authenticated users should be automatically redirected to the dashboard.

Use Clerk's default components and flows.

Do not create custom authentication forms.

Keep the implementation minimal and production-ready.

## Implementation

Wrap the root application with ClerkProvider.

Create:

- /sign-in
- /sign-up

using Clerk components.

Create route protection using Clerk middleware/proxy.

Public Routes:

- /sign-in
- /sign-up

Protected Routes:

- /dashboard
- /workflows/*
- all future application routes

Update root route:

- authenticated users → /dashboard
- unauthenticated users → /sign-in

Add UserButton to the application navbar.

Keep Clerk default profile management.

Do not customize Clerk internals.

Use existing environment variables.

## Dependencies

Clerk SDK

## Check When Done

- ClerkProvider configured
- Route protection works
- Sign in page works
- Sign up page works
- Root redirect works
- UserButton visible after login
- Build passes