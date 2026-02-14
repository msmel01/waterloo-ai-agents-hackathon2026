import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ScreeningRoom } from '../components/ScreeningRoom';
import { fetchLivekitToken } from '../api/livekitToken';
import type { AuthState } from '../types';

export function ChatScreen() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [isJoining, setIsJoining] = useState(true);

  const displayName = localStorage.getItem('suitor_name') || 'Suitor';
  const dateName = slug ? slug.charAt(0).toUpperCase() + slug.slice(1) : 'Date';

  useEffect(() => {
    let cancelled = false;

    async function join() {
      try {
        // TODO: Wire to backend - pass dateId/slug for room
        const token = await fetchLivekitToken(`${displayName}-${slug ?? 'default'}`);
        if (!cancelled) {
          setAuth({ token, displayName });
        }
      } catch {
        // Stub: use placeholder token
        if (!cancelled) {
          setAuth({
            token: `placeholder_token_${displayName}_${Date.now()}`,
            displayName,
          });
        }
      } finally {
        if (!cancelled) setIsJoining(false);
      }
    }

    join();
    return () => {
      cancelled = true;
    };
  }, [displayName, slug]);

  const handleLeave = () => {
    setAuth(null);
    navigate('/dates');
  };

  if (isJoining) {
    return (
      <div className="min-h-screen bg-win-bg flex items-center justify-center">
        <p className="text-win-text text-sm">Connecting to {dateName}&apos;s hotline…</p>
      </div>
    );
  }

  if (!auth) {
    return null;
  }

  return <ScreeningRoom auth={auth} onLeave={handleLeave} dateName={dateName} />;
}
