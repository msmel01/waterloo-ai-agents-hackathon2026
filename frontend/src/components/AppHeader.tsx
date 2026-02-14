import { useAuth, SignOutButton } from '@clerk/clerk-react';

interface AppHeaderProps {
  /** Optional extra content to show in the header (e.g. back link) */
  children?: React.ReactNode;
}

export function AppHeader({ children }: AppHeaderProps) {
  const { isSignedIn } = useAuth();

  return (
    <header className="w-full max-w-5xl mx-auto mb-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 min-w-0">
          {children}
          <h1 className="text-win-textMuted text-sm font-medium uppercase tracking-wider">
            Valentine Hotline
          </h1>
          <div className="h-px bg-win-border mt-1" />
        </div>
        {isSignedIn && (
          <SignOutButton>
            <button
              type="button"
              className="flex-shrink-0 px-3 py-1.5 border border-win-border text-win-textMuted text-xs hover:bg-win-border hover:text-win-text transition-colors"
            >
              Sign out
            </button>
          </SignOutButton>
        )}
      </div>
    </header>
  );
}
