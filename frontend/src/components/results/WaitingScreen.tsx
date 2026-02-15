import { useEffect, useState } from 'react';

const MESSAGES = [
  'Our Heart is reviewing your conversation...',
  'Analyzing your chemistry...',
  'Almost ready...',
];

export function WaitingScreen() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = window.setInterval(() => {
      setIndex((prev) => (prev + 1) % MESSAGES.length);
    }, 1800);
    return () => window.clearInterval(id);
  }, []);

  return (
    <section className="m6-card text-center space-y-4">
      <div className="m6-heart-loader" aria-hidden>
        <span>❤</span>
      </div>
      <h2 className="text-xl font-semibold text-white">Analyzing your interview</h2>
      <p className="text-sm text-rose-100 min-h-5">{MESSAGES[index]}</p>
      <div className="m6-progress-shell">
        <div className="m6-progress-line" />
      </div>
    </section>
  );
}
