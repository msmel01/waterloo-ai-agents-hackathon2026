import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDashboardAuth } from '../../hooks/useDashboardAuth';

export function DashboardLogin() {
  const navigate = useNavigate();
  const { login } = useDashboardAuth();
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(key);
      navigate('/dashboard');
    } catch (_err) {
      setError('Invalid key. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >
        <h1 className="text-2xl font-bold text-slate-900">Heart Dashboard</h1>
        <p className="mt-2 text-sm text-slate-600">
          Enter your admin key to view screening results.
        </p>
        <input
          type="password"
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="Dashboard API key"
          className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
          required
        />
        {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="mt-4 w-full rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60"
        >
          {loading ? 'Checking...' : 'Enter Dashboard'}
        </button>
      </form>
    </div>
  );
}
