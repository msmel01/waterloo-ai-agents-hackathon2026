import { useAuth } from '@clerk/clerk-react';
import { useEffect } from 'react';

import { setAuthToken } from '../api/axiosInstance';

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
      setAuthToken(null);
      return;
    }

    void syncToken();
    intervalId = window.setInterval(() => {
      void syncToken();
    }, 30_000);

    return () => {
      mounted = false;
      if (intervalId !== null) {
        window.clearInterval(intervalId);
      }
    };
  }, [getToken, isSignedIn]);
}
