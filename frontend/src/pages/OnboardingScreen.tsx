import { Link } from 'react-router-dom';
import { useAuth } from '@clerk/clerk-react';
import { Window } from '../components/Window';
import { AppHeader } from '../components/AppHeader';

export function OnboardingScreen() {
  const { isSignedIn } = useAuth();

  return (
    <div className="min-h-screen bg-win-bg flex flex-col items-center py-6 px-4">
      <div className="w-full max-w-6xl">
        <AppHeader />
      </div>

      <div className="w-full max-w-6xl flex flex-col gap-4 flex-1">
        {/* Welcome window */}
        <Window title="ValentineHotline.exe" icon="phone">
          <div className="text-center">
            <p className="text-gray-500 text-xs mb-2">EST. 2026</p>
            <h2 className="text-2xl font-bold">
              <span className="text-gray-900">Valentine</span>{' '}
              <span className="text-win-titlebar">Hotline</span>
            </h2>
            <p className="text-gray-600 text-sm mt-2 leading-relaxed max-w-md mx-auto">
              A virtual voice assistant that plans, books, and perfects your dream date — so you can focus on the butterflies.
            </p>
          </div>
        </Window>

        {/* CTA: Sign up/in or Go To Chats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1">
          <Window title="About.exe" icon="info">
            <div className="space-y-3">
              <h3 className="text-gray-800 font-semibold text-sm">Product Overview</h3>
              <p className="text-gray-600 text-sm leading-relaxed">
                Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
              </p>
              <p className="text-gray-600 text-sm leading-relaxed">
                Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
              </p>
              <h3 className="text-gray-800 font-semibold text-sm pt-2">Key Features</h3>
              <ul className="text-gray-600 text-sm space-y-1 list-disc list-inside">
                <li>Placeholder feature one</li>
                <li>Placeholder feature two</li>
                <li>Placeholder feature three</li>
              </ul>
            </div>
          </Window>

          {isSignedIn ? (
            <Window title="Welcome.exe" icon="person">
              <div className="flex flex-col gap-4">
                <p className="text-gray-600 text-sm">
                  You&apos;re signed in. Browse dates and start a chat.
                </p>
                <Link
                  to="/chats"
                  className="w-full py-2.5 bg-win-titlebar text-white text-sm font-medium text-center hover:bg-win-titlebarLight transition-colors"
                >
                  Go To Chats
                </Link>
              </div>
            </Window>
          ) : (
            <Window title="Get Started.exe" icon="person">
              <div className="flex flex-col gap-4">
                <p className="text-gray-600 text-sm">
                  Sign in or create an account to browse dates and book chats.
                </p>
                <div className="flex flex-col gap-3">
                  <Link
                    to="/sign-in"
                    className="w-full py-2.5 bg-win-titlebar text-white text-sm font-medium text-center hover:bg-win-titlebarLight transition-colors"
                  >
                    Sign in
                  </Link>
                  <Link
                    to="/sign-up"
                    className="w-full py-2.5 border border-win-titlebar text-win-titlebar text-sm font-medium text-center hover:bg-win-titlebar/10 transition-colors"
                  >
                    Sign up
                  </Link>
                </div>
              </div>
            </Window>
          )}
        </div>

        {/* Built with - full width */}
        <Window title="BuiltWith.exe" icon="info">
          <p className="text-gray-600 text-sm">
            Built with [placeholder for logos] — LiveKit, Clerk, Vercel, and more.
          </p>
        </Window>
      </div>
    </div>
  );
}
