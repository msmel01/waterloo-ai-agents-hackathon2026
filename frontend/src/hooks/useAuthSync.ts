import { useAuth } from '@clerk/clerk-react';
import { useEffect } from 'react';

import { setAuthToken } from '../api/axiosInstance';

export function useAuthSync() {
  const { getToken, isSignedIn } = useAuth();

  useEffect(() => {
    let mounted = true;

    if (!isSignedIn) {
      setAuthToken(null);
      return;
    }

    getToken()
      .then((token) => {
        if (!mounted) {
          return;
        }
        setAuthToken(token ?? null);
      })
      .catch(() => {
        if (mounted) {
          setAuthToken(null);
        }
      });

    return () => {
      mounted = false;
    };
  }, [getToken, isSignedIn]);
}
