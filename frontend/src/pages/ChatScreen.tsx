import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { AxiosError } from 'axios';
import { useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';

import {
  useGetSessionStatusApiV1SessionsIdStatusGet,
  usePreCheckApiV1SessionsPreCheckGet,
  useStartSessionApiV1SessionsStartPost,
} from '../api/generated/sessions/sessions';
import { useGetMyProfileApiV1SuitorsMeGet } from '../api/generated/suitors/suitors';
import { ScreeningRoom } from '../components/ScreeningRoom';
import type { AuthState } from '../types';

export function ChatScreen() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { isSignedIn } = useAuth();

  const [auth, setAuth] = useState<AuthState | null>(null);
  const [blockingReason, setBlockingReason] = useState<string | null>(null);

  const hasStartedRef = useRef(false);

  const profileQuery = useGetMyProfileApiV1SuitorsMeGet({
    query: { enabled: !!isSignedIn },
  });
  const preCheckQuery = usePreCheckApiV1SessionsPreCheckGet({
    query: { enabled: !!isSignedIn, refetchInterval: 15_000 },
  });

  const startSession = useStartSessionApiV1SessionsStartPost();

  const sessionStatusQuery = useGetSessionStatusApiV1SessionsIdStatusGet(
    auth?.sessionId ?? '',
    {
      query: {
        enabled: !!auth?.sessionId,
        refetchInterval: (query) => {
          const status = query.state.data?.status;
          if (!status || ['completed', 'failed', 'expired', 'cancelled', 'scored'].includes(status)) {
            return false;
          }
          return 15_000;
        },
      },
    }
  );

  useEffect(() => {
    if (!isSignedIn) {
      navigate('/sign-in', { replace: true });
    }
  }, [isSignedIn, navigate]);

  useEffect(() => {
    if (!isSignedIn || !slug || hasStartedRef.current) {
      return;
    }
    if (profileQuery.isLoading || preCheckQuery.isLoading) {
      return;
    }

    const profile = profileQuery.data;
    const preCheck = preCheckQuery.data;

    if (!profile?.is_profile_complete) {
        setBlockingReason('Please complete your profile before starting an interview.');
      navigate('/sign-up', { replace: true });
      return;
    }

    if (preCheckQuery.isError) {
      const error = preCheckQuery.error as AxiosError<{ detail?: string }>;
      const detail = error.response?.data?.detail;
      setBlockingReason(detail || 'Could not validate interview eligibility.');
      hasStartedRef.current = false;
      return;
    }

    if (!preCheck) {
      return;
    }

    if (!preCheck.can_start && !preCheck.active_session_id) {
      setBlockingReason(preCheck.reason ?? 'You cannot start an interview right now.');
      return;
    }

    hasStartedRef.current = true;
    startSession
      .mutateAsync({ data: { heart_slug: slug } })
      .then((response) => {
        setAuth({
          token: response.livekit_token,
          livekitUrl: response.livekit_url,
          sessionId: response.session_id,
          displayName: profile?.name || 'Suitor',
        });
        toast.success(response.message || 'Session ready');
      })
      .catch((error) => {
        hasStartedRef.current = false;
        const axiosError = error as AxiosError<{ detail?: string }>;
        const status = axiosError.response?.status;
        const detail = axiosError.response?.data?.detail;

        if (status === 400) {
          setBlockingReason(detail || 'Please complete your profile first.');
          navigate('/sign-up');
          return;
        }
        if (status === 429) {
          setBlockingReason(detail || 'Daily interview limit reached. Try again tomorrow.');
          return;
        }
        if (status === 503) {
          setBlockingReason(detail || 'Interviews are currently paused.');
          return;
        }

        setBlockingReason(detail || 'Could not start interview session. Please retry.');
      });
  }, [
    isSignedIn,
    slug,
    profileQuery.data,
    profileQuery.isLoading,
    preCheckQuery.data,
    preCheckQuery.error,
    preCheckQuery.isError,
    preCheckQuery.isLoading,
    startSession,
    navigate,
  ]);

  useEffect(() => {
    const status = sessionStatusQuery.data?.status;
    if (!status) {
      return;
    }
    if (['completed', 'failed', 'expired', 'cancelled', 'scored'].includes(status)) {
      toast.info(`Session ended (${status}).`);
      navigate('/chats', { replace: true });
    }
  }, [sessionStatusQuery.data?.status, navigate]);

  const handleLeave = () => {
    setAuth(null);
    navigate('/chats');
  };

  if (profileQuery.isLoading || preCheckQuery.isLoading || startSession.isPending) {
    return (
      <div className="min-h-screen bg-win-bg flex items-center justify-center">
        <p className="text-win-text text-sm">Preparing your hotline session…</p>
      </div>
    );
  }

  if (blockingReason) {
    return (
      <div className="min-h-screen bg-win-bg flex items-center justify-center px-4">
        <div className="max-w-md text-center">
          <p className="text-win-text text-sm mb-4">{blockingReason}</p>
          <button
            type="button"
            onClick={() => navigate('/chats')}
            className="px-4 py-2 bg-win-titlebar text-white text-sm border border-palette-orchid shadow-bevel"
          >
            Back to chats
          </button>
        </div>
      </div>
    );
  }

  if (!auth) {
    return null;
  }

  return (
    <ScreeningRoom
      auth={auth}
      onLeave={handleLeave}
      dateName={slug ? slug.charAt(0).toUpperCase() + slug.slice(1) : 'Date'}
      sessionStatus={sessionStatusQuery.data}
    />
  );
}
