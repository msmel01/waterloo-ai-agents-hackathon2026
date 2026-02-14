import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useSignUp } from '@clerk/clerk-react';
import { toast } from 'sonner';
import { Window } from '../components/Window';
import { AppHeader } from '../components/AppHeader';
import { syncSuitorProfile } from '../api/suitorProfile';

const inputClass =
  'w-full px-3 py-2 bg-white border border-gray-400 text-gray-900 placeholder-gray-500 text-sm focus:outline-none focus:border-win-titlebar';
const labelClass = 'block text-gray-600 text-sm mb-1';

export function SignUpScreen() {
  const navigate = useNavigate();
  const { isLoaded, signUp, setActive } = useSignUp();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [gender, setGender] = useState('');
  const [orientation, setOrientation] = useState('');
  const [age, setAge] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [code, setCode] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!isLoaded || !signUp) return;

    const ageNum = parseInt(age, 10);
    if (isNaN(ageNum) || ageNum < 18) {
      setError('You must be at least 18 years old to sign up.');
      return;
    }

    setIsSubmitting(true);
    try {
      await signUp.create({ emailAddress: email, password });
      await signUp.prepareEmailAddressVerification({ strategy: 'email_code' });
      setVerifying(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Sign up failed';
      setError(typeof msg === 'string' ? msg : 'Something went wrong');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerify = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsVerifying(true);
    if (!isLoaded || !signUp) {
      setIsVerifying(false);
      return;
    }

    try {
      const res = await signUp.attemptEmailAddressVerification({ code });

      if (res.status === 'complete' && res.createdSessionId) {
        await syncSuitorProfile({ name: name.trim(), gender, orientation, age });
        toast.success('Verification successful');
        await setActive({
          session: res.createdSessionId,
          redirectUrl: `${window.location.origin}/chats`,
        });
        navigate('/chats', { replace: true });
      } else if (res.status === 'missing_requirements') {
        const missing = (res as { missingFields?: string[] }).missingFields ?? [];
        setError(`Missing required: ${missing.join(', ')}. Please fill in all required fields.`);
      } else {
        setError('Verification completed but could not sign in. Try signing in with your new account.');
        setVerifying(false);
        setCode('');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setIsVerifying(false);
    }
  };

  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-win-bg flex items-center justify-center">
        <p className="text-win-textMuted text-sm">Loading…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-win-bg flex flex-col items-center justify-center py-6 px-4">
      <div className="w-full max-w-md mb-6">
        <AppHeader />
      </div>

      <div className="w-full max-w-md">
        <Window title="SignUp.exe" icon="person">
          <form
            onSubmit={verifying ? handleVerify : handleSubmit}
            className="space-y-4"
          >
            {error && (
              <p className="text-red-600 text-sm" role="alert">
                {error}
              </p>
            )}

            {verifying ? (
              <>
                <p className="text-gray-600 text-sm">
                  A verification code has been sent to your email.
                </p>
                <div>
                  <label htmlFor="code" className={labelClass}>
                    Verification code
                  </label>
                  <input
                    id="code"
                    type="text"
                    inputMode="numeric"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className={inputClass}
                    placeholder="Enter code"
                    required
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label htmlFor="email" className={labelClass}>
                    Email
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={inputClass}
                    placeholder="your@email.com"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="name" className={labelClass}>
                    Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className={inputClass}
                    placeholder="Your full name"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="password" className={labelClass}>
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={inputClass}
                    placeholder="Choose a password"
                    required
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                  <div>
                    <label htmlFor="age" className={labelClass}>
                      Age
                    </label>
                    <input
                      id="age"
                      type="number"
                      min={18}
                      value={age}
                      onChange={(e) => setAge(e.target.value)}
                      placeholder="18+"
                      className={inputClass}
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="orientation" className={labelClass}>
                      Sexual Orientation
                    </label>
                    <div className="relative">
                      <select
                        id="orientation"
                        value={orientation}
                        onChange={(e) => setOrientation(e.target.value)}
                        className={`${inputClass} pr-8 appearance-none`}
                      >
                        <option value="">Select</option>
                        <option value="Straight">Straight</option>
                        <option value="Gay">Gay</option>
                        <option value="Bisexual">Bisexual</option>
                        <option value="Other">Other</option>
                      </select>
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 pointer-events-none">
                        ▾
                      </span>
                    </div>
                  </div>
                  <div className="sm:col-span-2">
                    <label htmlFor="gender" className={labelClass}>
                      Gender
                    </label>
                    <div className="relative">
                      <select
                        id="gender"
                        value={gender}
                        onChange={(e) => setGender(e.target.value)}
                        className={`${inputClass} pr-8 appearance-none`}
                      >
                        <option value="">Select</option>
                        <option value="Man">Man</option>
                        <option value="Woman">Woman</option>
                        <option value="Non-binary">Non-binary</option>
                        <option value="Other">Other</option>
                      </select>
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 pointer-events-none">
                        ▾
                      </span>
                    </div>
                  </div>
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={isSubmitting || isVerifying}
              className="w-full py-2.5 bg-win-titlebar text-white text-sm font-medium hover:bg-win-titlebarLight transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Creating account…' : isVerifying ? 'Verifying…' : verifying ? 'Verify' : 'Create account'}
            </button>
          </form>
        </Window>

        <p className="text-win-textMuted text-sm text-center mt-4">
          Already have an account?{' '}
          <Link to="/sign-in" className="text-win-titlebar hover:underline">
            Sign in
          </Link>
        </p>
        <p className="text-win-textMuted text-sm text-center mt-2">
          <Link to="/" className="hover:text-win-text transition-colors">
            ← Back to home
          </Link>
        </p>
      </div>
    </div>
  );
}
