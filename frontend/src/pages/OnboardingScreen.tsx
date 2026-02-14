import { FormEvent, useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth, useUser } from '@clerk/clerk-react';
import { Window } from '../components/Window';

export function OnboardingScreen() {
  const navigate = useNavigate();
  const { isSignedIn } = useAuth();
  const { user } = useUser();
  const [name, setName] = useState('');
  const [gender, setGender] = useState('');
  const [age, setAge] = useState('');
  const [orientation, setOrientation] = useState('');

  useEffect(() => {
    if (user?.fullName) {
      setName(user.fullName);
    } else if (user?.firstName) {
      setName(user.firstName);
    }
  }, [user]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      localStorage.setItem('suitor_name', name.trim());
      localStorage.setItem('suitor_gender', gender);
      localStorage.setItem('suitor_age', age);
      localStorage.setItem('suitor_orientation', orientation);
      navigate('/dates');
    }
  };

  return (
    <div className="min-h-screen bg-win-bg flex flex-col items-center py-6 px-4">
      {/* Header */}
      <header className="w-full max-w-6xl mb-6">
        <h1 className="text-win-textMuted text-sm font-medium uppercase tracking-wider">
          Valentine Hotline
        </h1>
        <div className="h-px bg-win-border mt-1" />
      </header>

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

        {/* Two-column: Product info + NewUser form or Auth CTA */}
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
            <Window title="NewUser.exe" icon="person">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="name" className="block text-gray-600 text-sm mb-1">
                      Name
                    </label>
                    <input
                      id="name"
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Your full name"
                      className="w-full px-3 py-2 bg-white border border-gray-400 text-gray-900 placeholder-gray-500 text-sm focus:outline-none focus:border-win-titlebar"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="age" className="block text-gray-600 text-sm mb-1">
                      Age
                    </label>
                    <input
                      id="age"
                      type="text"
                      value={age}
                      onChange={(e) => setAge(e.target.value)}
                      placeholder="18+"
                      className="w-full px-3 py-2 bg-white border border-gray-400 text-gray-900 placeholder-gray-500 text-sm focus:outline-none focus:border-win-titlebar"
                    />
                  </div>
                  <div>
                    <label htmlFor="orientation" className="block text-gray-600 text-sm mb-1">
                      Sexual Orientation
                    </label>
                    <div className="relative">
                      <select
                        id="orientation"
                        value={orientation}
                        onChange={(e) => setOrientation(e.target.value)}
                        className="w-full px-3 py-2 pr-8 bg-white border border-gray-400 text-gray-900 text-sm focus:outline-none focus:border-win-titlebar appearance-none"
                      >
                        <option value="">Select</option>
                        <option value="Straight">Straight</option>
                        <option value="Gay">Gay</option>
                        <option value="Bisexual">Bisexual</option>
                        <option value="Other">Other</option>
                      </select>
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 pointer-events-none">▾</span>
                    </div>
                  </div>
                  <div>
                    <label htmlFor="gender" className="block text-gray-600 text-sm mb-1">
                      Gender
                    </label>
                    <div className="relative">
                      <select
                        id="gender"
                        value={gender}
                        onChange={(e) => setGender(e.target.value)}
                        className="w-full px-3 py-2 pr-8 bg-white border border-gray-400 text-gray-900 text-sm focus:outline-none focus:border-win-titlebar appearance-none"
                      >
                        <option value="">Select</option>
                        <option value="Man">Man</option>
                        <option value="Woman">Woman</option>
                        <option value="Non-binary">Non-binary</option>
                        <option value="Other">Other</option>
                      </select>
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 pointer-events-none">▾</span>
                    </div>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={!name.trim()}
                  className="mt-4 w-full py-2.5 bg-win-titlebar text-white text-sm font-medium disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed hover:bg-win-titlebarLight transition-colors"
                >
                  Continue
                </button>
              </form>
            </Window>
          ) : (
            <Window title="NewUser.exe" icon="person">
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
                    Create account
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
