type ErrorFallbackProps = {
  error?: Error;
};

export function ErrorFallback({ error }: ErrorFallbackProps) {
  return (
    <div className="min-h-screen bg-rose-50 flex items-center justify-center px-4">
      <div className="w-full max-w-lg rounded-2xl border border-rose-200 bg-white p-8 text-center shadow-sm">
        <h1 className="text-2xl font-semibold text-rose-700">Something went wrong</h1>
        <p className="mt-3 text-sm text-slate-600">
          An unexpected error occurred. Refresh the page to try again.
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          className="mt-6 rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700"
        >
          Refresh
        </button>
        {error ? (
          <p className="mt-4 break-all text-xs text-slate-500" role="status" aria-live="polite">
            {error.message}
          </p>
        ) : null}
      </div>
    </div>
  );
}
