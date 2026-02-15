import { useMemo } from 'react';
import { verifyDashboardKey } from '../api/dashboard';

const STORAGE_KEY = 'dashboard_api_key';

export function useDashboardAuth() {
  const apiKey = useMemo(() => localStorage.getItem(STORAGE_KEY), []);

  const isAuthenticated = Boolean(apiKey);

  const login = async (key: string) => {
    await verifyDashboardKey(key);
    localStorage.setItem(STORAGE_KEY, key);
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
  };

  return { apiKey, isAuthenticated, login, logout };
}
