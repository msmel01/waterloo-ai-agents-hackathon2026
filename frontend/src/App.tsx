import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { OnboardingScreen } from './pages/OnboardingScreen';
import { DatesGrid } from './pages/DatesGrid';
import { ProfileScreen } from './pages/ProfileScreen';
import { ChatScreen } from './pages/ChatScreen';
import { SignInScreen } from './pages/SignInScreen';
import { SignUpScreen } from './pages/SignUpScreen';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<OnboardingScreen />} />
        <Route path="/sign-in" element={<SignInScreen />} />
        <Route path="/sign-up" element={<SignUpScreen />} />
        <Route path="/dates" element={<DatesGrid />} />
        <Route path="/profile/:slug" element={<ProfileScreen />} />
        <Route path="/chat/:slug" element={<ChatScreen />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
