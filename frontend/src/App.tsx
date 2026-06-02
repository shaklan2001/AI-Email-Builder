import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { SignInPage } from "./pages/SignInPage";
import { SignUpPage } from "./pages/SignUpPage";
import { NewWorkflowPage } from "./pages/NewWorkflowPage";
import { WorkflowBuilderPage } from "./pages/WorkflowBuilderPage";
import { WorkflowReviewPage } from "./pages/WorkflowReviewPage";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { PublicRoute } from "./routes/PublicRoute";
import { RootRedirect } from "./routes/RootRedirect";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootRedirect />} />

        <Route element={<PublicRoute />}>
          <Route path="/sign-in" element={<SignInPage />} />
          <Route path="/sign-up" element={<SignUpPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/campaigns/new" element={<NewWorkflowPage />} />
            <Route path="/campaigns/:workflowId/review" element={<WorkflowReviewPage />} />
            <Route path="/campaigns/:workflowId" element={<WorkflowBuilderPage />} />
            {/* Legacy /workflows paths (same screens) */}
            <Route path="/workflows/new" element={<NewWorkflowPage />} />
            <Route path="/workflows/:workflowId/review" element={<WorkflowReviewPage />} />
            <Route path="/workflows/:workflowId" element={<WorkflowBuilderPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
