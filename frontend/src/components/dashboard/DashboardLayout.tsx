import type { ReactNode } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { PauseToggle } from './PauseToggle';

type Props = {
  active?: boolean;
  loadingStatus?: boolean;
  onToggleStatus?: (active: boolean) => void;
  children: ReactNode;
};

export function DashboardLayout({ children, active, loadingStatus, onToggleStatus }: Props) {
  const navigate = useNavigate();
  const logout = () => {
    localStorage.removeItem('dashboard_api_key');
    navigate('/dashboard/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-bold text-violet-600">Valentine Hotline Dashboard</h1>
            <nav className="hidden gap-3 text-sm md:flex">
              <NavLink
                to="/dashboard"
                end
                className={({ isActive }) =>
                  isActive ? 'font-semibold text-violet-600' : 'text-slate-600 hover:text-slate-900'
                }
              >
                Overview
              </NavLink>
              <NavLink
                to="/dashboard/sessions"
                className={({ isActive }) =>
                  isActive ? 'font-semibold text-violet-600' : 'text-slate-600 hover:text-slate-900'
                }
              >
                Sessions
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {typeof active === 'boolean' && onToggleStatus && (
              <PauseToggle
                active={active}
                isLoading={loadingStatus}
                onToggle={(next) => {
                  if (!next) {
                    const ok = window.confirm(
                      "Pause screening? New suitors won't be able to start interviews."
                    );
                    if (!ok) return;
                  }
                  onToggleStatus(next);
                }}
              />
            )}
            <button
              type="button"
              className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
              onClick={logout}
            >
              Logout
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
