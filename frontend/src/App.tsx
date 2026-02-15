import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy, type ReactElement } from 'react';
import { useAuthSync } from './hooks/useAuthSync';
import { ErrorBoundary } from './components/ErrorBoundary';
import { OfflineBanner } from './components/OfflineBanner';

const MarketingPage = lazy(() => import('./pages/MarketingPage').then((m) => ({ default: m.MarketingPage })));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage').then((m) => ({ default: m.PrivacyPage })));
const OnboardingScreen = lazy(() =>
  import('./pages/OnboardingScreen').then((m) => ({ default: m.OnboardingScreen }))
);
const DatesGrid = lazy(() => import('./pages/DatesGrid').then((m) => ({ default: m.DatesGrid })));
const ProfileScreen = lazy(() => import('./pages/ProfileScreen').then((m) => ({ default: m.ProfileScreen })));
const ChatScreen = lazy(() => import('./pages/ChatScreen').then((m) => ({ default: m.ChatScreen })));
const InterviewCompleteScreen = lazy(() =>
  import('./pages/InterviewCompleteScreen').then((m) => ({ default: m.InterviewCompleteScreen }))
);
const ResultsPage = lazy(() => import('./pages/results/ResultsPage').then((m) => ({ default: m.ResultsPage })));
const SignInScreen = lazy(() => import('./pages/SignInScreen').then((m) => ({ default: m.SignInScreen })));
const SignUpScreen = lazy(() => import('./pages/SignUpScreen').then((m) => ({ default: m.SignUpScreen })));
const DashboardLogin = lazy(() =>
  import('./pages/dashboard/DashboardLogin').then((m) => ({ default: m.DashboardLogin }))
);
const DashboardOverview = lazy(() =>
  import('./pages/dashboard/DashboardOverview').then((m) => ({ default: m.DashboardOverview }))
);
const DashboardSessions = lazy(() =>
  import('./pages/dashboard/DashboardSessions').then((m) => ({ default: m.DashboardSessions }))
);
const DashboardSessionDetail = lazy(() =>
  import('./pages/dashboard/DashboardSessionDetail').then((m) => ({ default: m.DashboardSessionDetail }))
);

function RequireDashboardAuth({ children }: { children: ReactElement }) {
  const hasKey = Boolean(sessionStorage.getItem('dashboard_api_key'));
  if (!hasKey) {
    return <Navigate to="/dashboard/login" replace />;
  }
  return children;
}

function App() {
  useAuthSync();

  return (
    <ErrorBoundary>
      <OfflineBanner />
      <BrowserRouter>
        <Suspense
          fallback={
            <div className="min-h-screen flex items-center justify-center bg-win-bg text-sm text-win-text">
              Loading…
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<MarketingPage />} />
            <Route path="/start" element={<OnboardingScreen />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/sign-in" element={<SignInScreen />} />
            <Route path="/sign-up" element={<SignUpScreen />} />
            <Route path="/chats" element={<DatesGrid />} />
            <Route path="/dates" element={<DatesGrid />} />
            <Route path="/profile/:slug" element={<ProfileScreen />} />
            <Route path="/chat/:slug" element={<ChatScreen />} />
            <Route path="/session/:sessionId/results" element={<ResultsPage />} />
            <Route path="/interview/:sessionId/complete" element={<InterviewCompleteScreen />} />
            <Route path="/dashboard/login" element={<DashboardLogin />} />
            <Route
              path="/dashboard"
              element={
                <RequireDashboardAuth>
                  <ErrorBoundary>
                    <DashboardOverview />
                  </ErrorBoundary>
                </RequireDashboardAuth>
              }
            />
            <Route
              path="/dashboard/sessions"
              element={
                <RequireDashboardAuth>
                  <ErrorBoundary>
                    <DashboardSessions />
                  </ErrorBoundary>
                </RequireDashboardAuth>
              }
            />
            <Route
              path="/dashboard/sessions/:id"
              element={
                <RequireDashboardAuth>
                  <ErrorBoundary>
                    <DashboardSessionDetail />
                  </ErrorBoundary>
                </RequireDashboardAuth>
              }
            />
            <Route path="/:slug" element={<ProfileScreen />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
