import { useEffect, useState } from 'react';

import type { VerdictValue } from '../../types/results';

interface VerdictRevealProps {
  verdict: VerdictValue;
}

export function VerdictReveal({ verdict }: VerdictRevealProps) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const id = window.setTimeout(() => setShow(true), 1200);
    return () => window.clearTimeout(id);
  }, []);

  return (
    <section className={`m6-card ${verdict === 'date' ? 'm6-card-date' : 'm6-card-nodate'}`}>
      <div className={`m6-reveal ${show ? 'is-visible' : ''}`}>
        <p className="text-xs uppercase tracking-widest opacity-75">Verdict</p>
        <h1 className="text-3xl md:text-4xl font-bold mt-2">
          {verdict === 'date' ? "IT'S A DATE! 💚" : 'Not This Time 💔'}
        </h1>
      </div>
    </section>
  );
}
