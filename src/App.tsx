import { useState } from 'react';
import { ConnectScreen } from './components/ConnectScreen';
import { ScreeningRoom } from './components/ScreeningRoom';
import { fetchLivekitToken } from './lib/livekitToken';
import type { AuthState } from './types';

function App() {
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleJoin = async (displayName: string) => {
    setIsJoining(true);
    setError(null);
    try {
      const token = await fetchLivekitToken(displayName);
      setAuth({ token, displayName });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get token');
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

  return (
    <>
      <ConnectScreen onJoin={handleJoin} isJoining={isJoining} />
      {error && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg bg-red-900/90 text-red-100 text-sm">
          {error}
        </div>
      )}
    </>
  );
}

export default App;
