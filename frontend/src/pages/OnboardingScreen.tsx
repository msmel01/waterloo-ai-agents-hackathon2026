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
          <img
            src="https://u.cubeupload.com/pixel_bridges/dc0valentinehotlineword.png"
            alt="Valentine Hotline"
            className="w-full min-h-[300px] max-h-[300px] object-cover object-center"
          />
        </Window>

        {/* CTA: Sign up/in or Go To Chats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1">
          <Window title="About.exe" icon="info">
            <div className="space-y-3">
              <p className="text-gray-600 text-sm leading-relaxed">
                Want a date with your crush?
              </p>
              <p className="text-gray-600 text-sm leading-relaxed">
                Call their Valentine Hotline, where you&apos;ll be screened by their mildly unhinged, deeply observant, slightly sarcastic AI assistant.
              </p>
              <p className="text-gray-600 text-sm leading-relaxed">
                Before you get access to their calendar, you will be thoroughly screened for red flags, compatibility, and Emotional Intelligence™.
              </p>
              <p className="text-gray-600 text-sm leading-relaxed">
                Be warned. It can hear the hesitation in your voice. It notices the confidence drop. It heard that nervous laugh. Everything you say will be used against you.
              </p>
              <p className="text-gray-600 text-sm leading-relaxed">
                If you pass?<br />
                Congratulations. A date is automatically booked.
              </p>
              <p className="text-gray-600 text-sm leading-relaxed">
                If you fail?<br />
                You&apos;ll receive a clear explanation of why you were denied access to the calendar. No hard feelings.
              </p>
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
