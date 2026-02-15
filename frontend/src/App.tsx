import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { OnboardingScreen } from './pages/OnboardingScreen';
import { DatesGrid } from './pages/DatesGrid';
import { ProfileScreen } from './pages/ProfileScreen';
import { ChatScreen } from './pages/ChatScreen';
import { InterviewCompleteScreen } from './pages/InterviewCompleteScreen';
import { ResultsPage } from './pages/results/ResultsPage';
import { SignInScreen } from './pages/SignInScreen';
import { SignUpScreen } from './pages/SignUpScreen';
import { useAuthSync } from './hooks/useAuthSync';

function App() {
  useAuthSync();

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<OnboardingScreen />} />
        <Route path="/sign-in" element={<SignInScreen />} />
        <Route path="/sign-up" element={<SignUpScreen />} />
        <Route path="/chats" element={<DatesGrid />} />
        <Route path="/dates" element={<DatesGrid />} />
        <Route path="/profile/:slug" element={<ProfileScreen />} />
        <Route path="/chat/:slug" element={<ChatScreen />} />
        <Route path="/session/:sessionId/results" element={<ResultsPage />} />
        <Route path="/interview/:sessionId/complete" element={<InterviewCompleteScreen />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
