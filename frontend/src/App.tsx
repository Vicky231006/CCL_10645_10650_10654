import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useAuth } from "./lib/auth";
import { Spinner } from "./components/ui";
import { AppLayout, PublicLayout } from "./components/Layout";

import { Landing } from "./pages/public/Landing";
import { Features } from "./pages/public/Features";
import { HowItWorks } from "./pages/public/HowItWorks";
import { Privacy } from "./pages/public/Privacy";
import { Terms } from "./pages/public/Terms";
import { Login } from "./pages/public/Login";
import { Signup } from "./pages/public/Signup";

import { Dashboard } from "./pages/app/Dashboard";
import { Onboarding } from "./pages/app/Onboarding";
import { ProfilePage } from "./pages/app/Profile";
import { Resumes } from "./pages/app/Resumes";
import { ResumeNew } from "./pages/app/ResumeNew";
import { ResumeDetail } from "./pages/app/ResumeDetail";
import { ResumeAnalyze } from "./pages/app/ResumeAnalyze";
import { Jobs } from "./pages/app/Jobs";
import { JobDetail } from "./pages/app/JobDetail";
import { MatchPage } from "./pages/app/Match";
import { CareerRoadmap } from "./pages/app/CareerRoadmap";
import { Projects } from "./pages/app/Projects";
import { Portfolio } from "./pages/app/Portfolio";
import { PortfolioPublic } from "./pages/app/PortfolioPublic";
import { CompanyInsights } from "./pages/app/CompanyInsights";
import { Applications } from "./pages/app/Applications";
import { SettingsPage } from "./pages/app/Settings";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Spinner label="Restoring your session" />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}

export function App() {
  return (
    <Routes>
      <Route element={<PublicLayout><Landing /></PublicLayout>} path="/" />
      <Route path="/features" element={<PublicLayout><Features /></PublicLayout>} />
      <Route path="/how-it-works" element={<PublicLayout><HowItWorks /></PublicLayout>} />
      <Route path="/privacy" element={<PublicLayout><Privacy /></PublicLayout>} />
      <Route path="/terms" element={<PublicLayout><Terms /></PublicLayout>} />
      <Route path="/login" element={<PublicLayout><Login /></PublicLayout>} />
      <Route path="/signup" element={<PublicLayout><Signup /></PublicLayout>} />

      <Route path="/p/:slug" element={<PortfolioPublic />} />

      <Route
        path="/app"
        element={
          <Protected>
            <AppLayout />
          </Protected>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="onboarding" element={<Onboarding />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="resumes" element={<Resumes />} />
        <Route path="resumes/new" element={<ResumeNew />} />
        <Route path="resumes/:id" element={<ResumeDetail />} />
        <Route path="resumes/:id/analyze" element={<ResumeAnalyze />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="jobs/:id" element={<JobDetail />} />
        <Route path="match" element={<MatchPage />} />
        <Route path="career-roadmap" element={<CareerRoadmap />} />
        <Route path="projects" element={<Projects />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="company-insights" element={<CompanyInsights />} />
        <Route path="applications" element={<Applications />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
