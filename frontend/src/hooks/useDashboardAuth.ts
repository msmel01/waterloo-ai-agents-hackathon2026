import { useMemo, useState } from 'react';
import { verifyDashboardKey } from '../api/dashboard';

const STORAGE_KEY = 'dashboard_api_key';

export function useDashboardAuth() {
  const [apiKey, setApiKey] = useState<string | null>(() =>
    sessionStorage.getItem(STORAGE_KEY)
  );

  const isAuthenticated = useMemo(() => Boolean(apiKey), [apiKey]);

  const login = async (key: string) => {
    await verifyDashboardKey(key);
    sessionStorage.setItem(STORAGE_KEY, key);
    setApiKey(key);
  };

  const logout = () => {
    sessionStorage.removeItem(STORAGE_KEY);
    setApiKey(null);
  };

  return { isAuthenticated, login, logout };
}
