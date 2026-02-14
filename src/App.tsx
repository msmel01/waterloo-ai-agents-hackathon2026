import { useState } from 'react';
import { ConnectScreen } from './components/ConnectScreen';
import { ScreeningRoom } from './components/ScreeningRoom';
import { fetchLivekitToken } from './lib/livekitToken';
import type { AuthState } from './types';

function App() {
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [isJoining, setIsJoining] = useState(false);

  const handleJoin = async (displayName: string) => {
    setIsJoining(true);
    try {
      // TODO: Wire to backend API when ready
      const token = await fetchLivekitToken(displayName);
      setAuth({ token, displayName });
    } catch {
      // Stub: never surface errors; backend will handle when connected
    } finally {
      setIsJoining(false);
    }
  };

  const handleLeave = () => {
    setAuth(null);
  };

  if (auth) {
    return <ScreeningRoom auth={auth} onLeave={handleLeave} />;
  }

  return <ConnectScreen onJoin={handleJoin} isJoining={isJoining} />;
}

export default App;
