import type { VerdictFeedback } from '../../types/results';

interface FeedbackDisplayProps {
  feedback: VerdictFeedback;
}

export function FeedbackDisplay({ feedback }: FeedbackDisplayProps) {
  return (
    <section className="m6-card space-y-4">
      <h3 className="text-white text-lg font-semibold">Your Feedback</h3>
      <blockquote className="border-l-4 border-rose-300 pl-4 text-rose-50 text-sm">
        {feedback.summary}
      </blockquote>

      <div>
        <p className="text-green-200 text-sm font-semibold">Strengths</p>
        <ul className="list-disc list-inside text-rose-50 text-sm space-y-1 mt-1">
          {feedback.strengths.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>

      <div>
        <p className="text-amber-200 text-sm font-semibold">Room to Grow</p>
        <ul className="list-disc list-inside text-rose-50 text-sm space-y-1 mt-1">
          {feedback.improvements.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>

      {feedback.favorite_moment ? (
        <div className="rounded bg-white/10 p-3 border border-white/20">
          <p className="text-xs uppercase text-rose-200 tracking-widest">Standout Moment</p>
          <p className="text-rose-50 text-sm mt-1">{feedback.favorite_moment}</p>
        </div>
      ) : null}
    </section>
  );
}
