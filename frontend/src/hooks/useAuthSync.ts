import { useAuth } from '@clerk/clerk-react';
import { useEffect } from 'react';

import { setAuthToken, setAuthTokenProvider } from '../api/axiosInstance';

export function useAuthSync() {
  const { getToken, isSignedIn } = useAuth();

  useEffect(() => {
    let mounted = true;
    let intervalId: number | null = null;

    const syncToken = async () => {
      try {
        const token = await getToken();
        if (!mounted) {
          return;
        }
        setAuthToken(token ?? null);
      } catch {
        if (mounted) {
          setAuthToken(null);
        }
      }
    };

    if (!isSignedIn) {
      setAuthTokenProvider(null);
      setAuthToken(null);
      return;
    }

    setAuthTokenProvider(async () => getToken({ skipCache: true }));
    void syncToken();
    intervalId = window.setInterval(() => {
      void syncToken();
    }, 30_000);

    return () => {
      mounted = false;
      setAuthTokenProvider(null);
      if (intervalId !== null) {
        window.clearInterval(intervalId);
      }
    };
  }, [getToken, isSignedIn]);
}
