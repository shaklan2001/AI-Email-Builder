import { lazy } from "react";

export const DashboardPage = lazy(() =>
  import("../pages/DashboardPage").then((module) => ({
    default: module.DashboardPage,
  })),
);

export const SignInPage = lazy(() =>
  import("../pages/SignInPage").then((module) => ({
    default: module.SignInPage,
  })),
);

export const SignUpPage = lazy(() =>
  import("../pages/SignUpPage").then((module) => ({
    default: module.SignUpPage,
  })),
);

export const NewWorkflowPage = lazy(() =>
  import("../pages/NewWorkflowPage").then((module) => ({
    default: module.NewWorkflowPage,
  })),
);

export const WorkflowBuilderPage = lazy(() =>
  import("../pages/WorkflowBuilderPage").then((module) => ({
    default: module.WorkflowBuilderPage,
  })),
);

export const WorkflowReviewPage = lazy(() =>
  import("../pages/WorkflowReviewPage").then((module) => ({
    default: module.WorkflowReviewPage,
  })),
);
