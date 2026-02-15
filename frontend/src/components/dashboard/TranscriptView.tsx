import { useState } from 'react';
import type { SessionDetail } from '../../types/dashboard';

type Props = {
  transcript: SessionDetail['transcript'];
};

export function TranscriptView({ transcript }: Props) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-base font-semibold text-slate-900">Conversation Transcript</h3>
      <div className="mt-4 space-y-4">
        {transcript.map((turn) => {
          const isExpanded = Boolean(expanded[turn.turn]);
          const answer = turn.answer || '';
          const shouldCollapse = answer.length > 260;
          const shown = shouldCollapse && !isExpanded ? `${answer.slice(0, 260)}...` : answer;
          return (
            <div key={turn.turn} className="rounded-lg border border-slate-200 p-3">
              <p className="text-sm font-semibold text-slate-800">🤖 Q{turn.turn}: {turn.question}</p>
              <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">👤 A{turn.turn}: {shown}</p>
              {shouldCollapse && (
                <button
                  type="button"
                  className="mt-1 text-xs font-medium text-violet-600"
                  onClick={() => setExpanded((prev) => ({ ...prev, [turn.turn]: !isExpanded }))}
                >
                  {isExpanded ? 'Show less' : 'Show more'}
                </button>
              )}
              <p className="mt-2 text-xs text-slate-500">
                {turn.timestamp ? new Date(turn.timestamp).toLocaleTimeString() : ''}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
