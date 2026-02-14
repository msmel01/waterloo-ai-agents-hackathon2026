import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useSignIn } from '@clerk/clerk-react';
import { toast } from 'sonner';
import { Window } from '../components/Window';

const inputClass =
  'w-full px-3 py-2 bg-white border border-gray-400 text-gray-900 placeholder-gray-500 text-sm focus:outline-none focus:border-win-titlebar';
const labelClass = 'block text-gray-600 text-sm mb-1';

export function SignInScreen() {
  const navigate = useNavigate();
  const { isLoaded, signIn, setActive } = useSignIn();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showSecondFactor, setShowSecondFactor] = useState(false);
  const [secondFactorStrategy, setSecondFactorStrategy] = useState<
    'totp' | 'phone_code' | 'backup_code' | null
  >(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [code, setCode] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    if (!isLoaded || !signIn) {
      setIsSubmitting(false);
      return;
    }

    try {
      const res = await signIn.create({ identifier: email, password });

      if (res.status === 'complete' && res.createdSessionId) {
        await setActive({
          session: res.createdSessionId,
          redirectUrl: `${window.location.origin}/dates`,
        });
        navigate('/dates', { replace: true });
        return;
      }

      if (res.status === 'needs_second_factor') {
        const factors = res.supportedSecondFactors ?? [];
        const totpFactor = factors.find((f) => f.strategy === 'totp');
        const phoneFactor = factors.find(
          (f) => f.strategy === 'phone_code' && 'phoneNumberId' in f
        );
        const backupFactor = factors.find((f) => f.strategy === 'backup_code');

        if (totpFactor) {
          setSecondFactorStrategy('totp');
          setShowSecondFactor(true);
        } else if (phoneFactor && 'phoneNumberId' in phoneFactor) {
          try {
            await signIn.prepareSecondFactor({
              strategy: 'phone_code',
              phoneNumberId: phoneFactor.phoneNumberId,
            });
            setSecondFactorStrategy('phone_code');
            setShowSecondFactor(true);
          } catch (prepErr) {
            setError(
              prepErr instanceof Error ? prepErr.message : 'Could not send SMS code'
            );
          }
        } else if (backupFactor) {
          setSecondFactorStrategy('backup_code');
          setShowSecondFactor(true);
        } else {
          setError(
            'Sign-in requires a second factor (authenticator app or SMS), but none is available. Please contact support.'
          );
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Sign in failed';
      setError(typeof msg === 'string' ? msg : 'Something went wrong');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSecondFactorSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsVerifying(true);
    if (!isLoaded || !signIn || !secondFactorStrategy) {
      setIsVerifying(false);
      return;
    }

    try {
      const res = await signIn.attemptSecondFactor({
        strategy: secondFactorStrategy,
        code,
      });

      if (res.status === 'complete' && res.createdSessionId) {
        toast.success('Verification successful');
        await setActive({
          session: res.createdSessionId,
          redirectUrl: `${window.location.origin}/dates`,
        });
        navigate('/dates', { replace: true });
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
      <header className="w-full max-w-md mb-6">
        <h1 className="text-win-textMuted text-sm font-medium uppercase tracking-wider">
          Valentine Hotline
        </h1>
        <div className="h-px bg-win-border mt-1" />
      </header>

      <div className="w-full max-w-md">
        <Window title="SignIn.exe" icon="person">
          <form
            onSubmit={showSecondFactor ? handleSecondFactorSubmit : handleSubmit}
            className="space-y-4"
          >
            {error && (
              <p className="text-red-600 text-sm" role="alert">
                {error}
              </p>
            )}

            {showSecondFactor ? (
              <>
                <p className="text-gray-600 text-sm">
                  {secondFactorStrategy === 'totp'
                    ? 'Enter the code from your authenticator app.'
                    : secondFactorStrategy === 'phone_code'
                      ? 'Enter the code sent to your phone.'
                      : 'Enter your backup code.'}
                </p>
                <div>
                  <label htmlFor="code" className={labelClass}>
                    {secondFactorStrategy === 'totp'
                      ? 'Authenticator code'
                      : 'Verification code'}
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
                  <label htmlFor="password" className={labelClass}>
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={inputClass}
                    placeholder="••••••••"
                    required
                  />
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={isSubmitting || isVerifying}
              className="w-full py-2.5 bg-win-titlebar text-white text-sm font-medium hover:bg-win-titlebarLight transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isVerifying
                ? 'Verifying…'
                : isSubmitting
                  ? 'Signing in…'
                  : showSecondFactor
                    ? 'Verify'
                    : 'Sign in'}
            </button>
          </form>
        </Window>

        <p className="text-win-textMuted text-sm text-center mt-4">
          Don&apos;t have an account?{' '}
          <Link to="/sign-up" className="text-win-titlebar hover:underline">
            Create account
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
