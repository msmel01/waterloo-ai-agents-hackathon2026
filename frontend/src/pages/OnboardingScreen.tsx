import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function OnboardingScreen() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [gender, setGender] = useState('');
  const [age, setAge] = useState('');
  const [orientation, setOrientation] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    // TODO: Wire to Clerk sign-up and backend when ready
    if (name.trim()) {
      localStorage.setItem('suitor_name', name.trim());
      localStorage.setItem('suitor_gender', gender);
      localStorage.setItem('suitor_age', age);
      localStorage.setItem('suitor_orientation', orientation);
      navigate('/dates');
    }
  };

  return (
    <div className="min-h-screen bg-y2k flex items-center justify-center p-4 relative">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <span className="absolute top-20 left-[15%] text-y2k-hotpink/40 text-2xl">✦</span>
        <span className="absolute top-32 right-[20%] text-y2k-cyan/50 text-xl">⋆</span>
      </div>

      <div className="w-full max-w-md relative z-10">
        <div
          className="border-4 border-y2k-hotpink bg-black/60 p-8 relative"
          style={{ boxShadow: '0 0 20px rgba(255,20,147,0.4)' }}
        >
          <h1 className="font-rochester text-5xl text-y2k-hotpink text-glow-pink mb-1 text-center">
            Valentine Hotline
          </h1>
          <p className="font-pixel text-lg text-y2k-cyan/90 mb-6 text-center">
            Welcome! Let&apos;s get to know you.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-semibold text-y2k-cyan/90 mb-1 uppercase">
                Name
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                className="w-full px-4 py-3 border-4 border-y2k-hotpink bg-black/80 text-y2k-cyan placeholder-stone-500 focus:outline-none focus:border-y2k-cyan font-pixel text-xl"
                required
              />
            </div>
            <div>
              <label htmlFor="gender" className="block text-sm font-semibold text-y2k-cyan/90 mb-1 uppercase">
                Gender
              </label>
              <input
                id="gender"
                type="text"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                placeholder="e.g. Man, Woman, Non-binary"
                className="w-full px-4 py-3 border-4 border-y2k-hotpink bg-black/80 text-y2k-cyan placeholder-stone-500 focus:outline-none focus:border-y2k-cyan font-pixel text-xl"
              />
            </div>
            <div>
              <label htmlFor="age" className="block text-sm font-semibold text-y2k-cyan/90 mb-1 uppercase">
                Age
              </label>
              <input
                id="age"
                type="text"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="Your age"
                className="w-full px-4 py-3 border-4 border-y2k-hotpink bg-black/80 text-y2k-cyan placeholder-stone-500 focus:outline-none focus:border-y2k-cyan font-pixel text-xl"
              />
            </div>
            <div>
              <label htmlFor="orientation" className="block text-sm font-semibold text-y2k-cyan/90 mb-1 uppercase">
                Sexual orientation
              </label>
              <input
                id="orientation"
                type="text"
                value={orientation}
                onChange={(e) => setOrientation(e.target.value)}
                placeholder="e.g. Straight, Gay, Bisexual"
                className="w-full px-4 py-3 border-4 border-y2k-hotpink bg-black/80 text-y2k-cyan placeholder-stone-500 focus:outline-none focus:border-y2k-cyan font-pixel text-xl"
              />
            </div>
            <div>
              <label htmlFor="username" className="block text-sm font-semibold text-y2k-cyan/90 mb-1 uppercase">
                Username (Clerk login)
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Choose a username"
                className="w-full px-4 py-3 border-4 border-y2k-hotpink bg-black/80 text-y2k-cyan placeholder-stone-500 focus:outline-none focus:border-y2k-cyan font-pixel text-xl"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-y2k-cyan/90 mb-1 uppercase">
                Password (Clerk login)
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Choose a password"
                className="w-full px-4 py-3 border-4 border-y2k-hotpink bg-black/80 text-y2k-cyan placeholder-stone-500 focus:outline-none focus:border-y2k-cyan font-pixel text-xl"
              />
            </div>
            <button
              type="submit"
              disabled={!name.trim()}
              className="w-full py-4 border-4 border-y2k-lime bg-y2k-hotpink disabled:bg-stone-800 disabled:border-stone-600 disabled:text-stone-500 disabled:cursor-not-allowed text-black font-pixel text-xl uppercase tracking-wider hover:shadow-neon-lime transition-all"
            >
              Continue
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
