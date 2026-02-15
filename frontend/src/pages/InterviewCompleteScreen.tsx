import { useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import {
  useGetSessionStatusApiV1SessionsIdStatusGet,
  useGetSessionVerdictApiV1SessionsIdVerdictGet,
} from '../api/generated/sessions/sessions';
import { AppHeader } from '../components/AppHeader';
import { Window } from '../components/Window';

function formatDuration(seconds?: number | null): string {
  if (seconds == null) {
    return '--';
  }
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${String(secs).padStart(2, '0')}`;
}

function ScoreBar({ label, value }: { label: string; value?: number | null }) {
  const safe = Math.max(0, Math.min(100, Math.round(value ?? 0)));
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-700 mb-1">
        <span>{label}</span>
        <span>{safe}</span>
      </div>
      <div className="h-2 bg-gray-200 border border-gray-300">
        <div
          className="h-full bg-win-titlebar transition-all duration-700"
          style={{ width: `${safe}%` }}
        />
      </div>
    </div>
  );
}

export function InterviewCompleteScreen() {
  const { sessionId = '' } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [showQuestions, setShowQuestions] = useState(false);

  const statusQuery = useGetSessionStatusApiV1SessionsIdStatusGet(sessionId, {
    query: {
      enabled: !!sessionId,
      refetchInterval: (query) => {
        const verdictStatus = query.state.data?.verdict_status;
        if (!verdictStatus) {
          return 5000;
        }
        if (verdictStatus === 'ready' || verdictStatus === 'failed') {
          return false;
        }
        return 5000;
      },
    },
  });

  const verdictQuery = useGetSessionVerdictApiV1SessionsIdVerdictGet(sessionId, {
    query: {
      enabled: statusQuery.data?.verdict_status === 'ready',
      retry: false,
    },
  });

  const waiting =
    !statusQuery.data ||
    (!statusQuery.data.has_verdict && statusQuery.data.verdict_status !== 'failed');

  const verdict = verdictQuery.data;
  const modifierMap = (verdict?.emotion_modifiers as Record<string, unknown> | null) ?? null;
  const verdictLabel = useMemo(() => {
    if (!verdict?.verdict) {
      return null;
    }
    return verdict.verdict === 'date' ? "IT'S A DATE" : 'NOT THIS TIME';
  }, [verdict?.verdict]);

  if (statusQuery.isLoading || waiting || verdictQuery.isLoading) {
    return (
      <div className="min-h-screen bg-win-bg flex flex-col py-6 px-4">
        <AppHeader />
        <main className="flex-1 max-w-xl mx-auto w-full mt-8">
          <Window title="Scoring.exe" icon="info">
            <div className="text-center space-y-4">
              <p className="text-lg text-gray-800 font-semibold">Analyzing your interview...</p>
              <div className="w-full h-3 border border-gray-300 bg-gray-200 overflow-hidden">
                <div className="h-full w-1/3 bg-win-titlebar animate-pulse" />
              </div>
              <p className="text-sm text-gray-600">
                Our AI is reviewing effort, creativity, intent, and emotional intelligence.
              </p>
              <div className="text-xs text-gray-700 border border-gray-300 bg-white p-3 text-left space-y-1">
                <p>Interview duration: {formatDuration(statusQuery.data?.duration_seconds)}</p>
                <p>
                  Questions answered: {statusQuery.data?.questions_asked ?? '--'} /
                  {statusQuery.data?.questions_total ?? '--'}
                </p>
              </div>
            </div>
          </Window>
        </main>
      </div>
    );
  }

  if (statusQuery.data?.verdict_status === 'failed') {
    return (
      <div className="min-h-screen bg-win-bg flex flex-col py-6 px-4">
        <AppHeader />
        <main className="flex-1 max-w-xl mx-auto w-full mt-8">
          <Window title="ScoringFailed.exe" icon="info">
            <div className="text-center space-y-4">
              <p className="text-lg text-gray-800 font-semibold">Something went wrong</p>
              <p className="text-sm text-gray-600">
                We could not score this interview. Please try again later.
              </p>
              <button
                type="button"
                onClick={() => navigate('/chats')}
                className="px-4 py-2 bg-win-titlebar text-white text-sm border border-palette-orchid shadow-bevel"
              >
                View My Sessions
              </button>
            </div>
          </Window>
        </main>
      </div>
    );
  }

  if (verdictQuery.isError || !verdict) {
    return (
      <div className="min-h-screen bg-win-bg flex flex-col py-6 px-4">
        <AppHeader />
        <main className="flex-1 max-w-xl mx-auto w-full mt-8">
          <Window title="Verdict.exe" icon="info">
            <div className="text-center space-y-4">
              <p className="text-sm text-gray-700">Verdict is not available yet.</p>
              <Link
                to="/chats"
                className="inline-block px-4 py-2 bg-win-titlebar text-white text-sm border border-palette-orchid shadow-bevel"
              >
                Back to sessions
              </Link>
            </div>
          </Window>
        </main>
      </div>
    );
  }

  const finalScore = Math.round(verdict.final_score ?? verdict.weighted_total ?? 0);

  return (
    <div className="min-h-screen bg-win-bg flex flex-col py-6 px-4">
      <AppHeader />
      <main className="flex-1 max-w-2xl mx-auto w-full mt-6 space-y-4">
        <Window title="VerdictReveal.exe" icon="person">
          <div className="space-y-4">
            <div className="text-center space-y-1">
              <p className="text-2xl font-bold text-gray-800">{verdictLabel}</p>
              <p className="text-sm text-gray-700">Score: {finalScore}/100</p>
            </div>

            <div className="space-y-3">
              <ScoreBar label="Effort" value={verdict.effort_score} />
              <ScoreBar label="Creativity" value={verdict.creativity_score} />
              <ScoreBar label="Intent" value={verdict.intent_clarity_score} />
              <ScoreBar label="Emotional IQ" value={verdict.emotional_intelligence_score} />
            </div>

            <div className="text-sm text-gray-700 space-y-1">
              <p>Voice modifier: {Number(modifierMap?.voice_modifier ?? 0)}</p>
              {verdict.emotion_modifier_reasons?.length ? (
                <ul className="list-disc ml-5 text-xs text-gray-600">
                  {verdict.emotion_modifier_reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              ) : null}
            </div>

            {verdict.feedback_text ? (
              <p className="text-sm text-gray-700 border border-gray-300 bg-white p-3">
                {verdict.feedback_text}
              </p>
            ) : null}

            {verdict.feedback_strengths?.length ? (
              <div>
                <p className="text-sm font-semibold text-gray-800 mb-1">Strengths</p>
                <ul className="list-disc ml-5 text-xs text-gray-600 space-y-1">
                  {verdict.feedback_strengths.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {verdict.feedback_improvements?.length ? (
              <div>
                <p className="text-sm font-semibold text-gray-800 mb-1">Could improve</p>
                <ul className="list-disc ml-5 text-xs text-gray-600 space-y-1">
                  {verdict.feedback_improvements.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            <div>
              <button
                type="button"
                className="text-xs text-win-titlebar underline"
                onClick={() => setShowQuestions((prev) => !prev)}
              >
                {showQuestions ? 'Hide' : 'Show'} question-by-question breakdown
              </button>
              {showQuestions && verdict.per_question_scores?.length ? (
                <div className="mt-3 space-y-2">
                  {verdict.per_question_scores.map((item, idx) => {
                    const row = (item ?? {}) as Record<string, unknown>;
                    const questionIndex =
                      typeof row.question_index === 'number' ? row.question_index : idx;
                    return (
                      <div
                        key={`${questionIndex}-${idx}`}
                        className="border border-gray-300 bg-white p-3 text-xs text-gray-700"
                      >
                        <p className="font-semibold mb-1">
                          Q{questionIndex + 1}: {(row.question_text as string) ?? 'Question'}
                        </p>
                        <p>
                          Effort: {(row.effort as number | string | undefined) ?? '-'} •
                          Creativity: {(row.creativity as number | string | undefined) ?? '-'} •
                          Intent: {(row.intent_clarity as number | string | undefined) ?? '-'} •
                          EQ:{' '}
                          {(row.emotional_intelligence as number | string | undefined) ?? '-'}
                        </p>
                        {row.emotion_context ? (
                          <p className="mt-1">Emotion: {String(row.emotion_context)}</p>
                        ) : null}
                        {row.note ? <p className="mt-1">Note: {String(row.note)}</p> : null}
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </div>

            <div className="flex gap-2 pt-2">
              {verdict.verdict === 'date' ? (
                <button
                  type="button"
                  onClick={() => navigate('/chats')}
                  className="px-4 py-2 bg-win-titlebar text-white text-sm border border-palette-orchid shadow-bevel"
                >
                  Book a Date (Soon)
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => navigate('/chats')}
                className="px-4 py-2 border border-palette-orchid bg-palette-sand text-sm text-gray-800 shadow-bevel"
              >
                View My Sessions
              </button>
            </div>
          </div>
        </Window>
      </main>
    </div>
  );
}
