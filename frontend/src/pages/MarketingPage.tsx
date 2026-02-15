import { Link } from 'react-router-dom';
import { useEffect } from 'react';

const HEART_SLUG = import.meta.env.VITE_HEART_SLUG || 'melika';

export function MarketingPage() {
  useEffect(() => {
    const previousTitle = document.title;
    document.title = 'Valentine Hotline — AI-Powered Dating Screening';

    const setMeta = (name: string, content: string, property = false) => {
      const selector = property ? `meta[property="${name}"]` : `meta[name="${name}"]`;
      let tag = document.head.querySelector(selector) as HTMLMetaElement | null;
      if (!tag) {
        tag = document.createElement('meta');
        if (property) tag.setAttribute('property', name);
        else tag.setAttribute('name', name);
        document.head.appendChild(tag);
      }
      tag.setAttribute('content', content);
    };

    setMeta(
      'description',
      'Let AI screen your Valentine suitors with voice interviews, smart scoring, and instant date booking.'
    );
    setMeta('og:title', 'Valentine Hotline 💘', true);
    setMeta('og:description', 'AI screens your dates so you do not have to.', true);
    setMeta('og:url', window.location.origin, true);
    setMeta('og:type', 'website', true);
    setMeta('twitter:card', 'summary_large_image');

    return () => {
      document.title = previousTitle;
    };
  }, []);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,#ffe0e8_0%,#fff7f3_42%,#f3f4f6_100%)] text-slate-800">
      <section className="mx-auto max-w-5xl px-6 py-16 text-center">
        <p className="text-sm uppercase tracking-[0.25em] text-rose-600">Valentine Hotline</p>
        <h1 className="mt-4 text-5xl font-black leading-tight md:text-6xl">
          Let AI Screen
          <br />
          Your Suitors
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600">
          Voice-first interviews, personality-matched questioning, smart transcript scoring, and instant date booking for qualified matches.
        </p>
        <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <Link
            to={`/profile/${HEART_SLUG}`}
            className="rounded-lg bg-rose-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-rose-700"
          >
            Try the Demo
          </Link>
          <Link
            to="/start"
            className="rounded-lg border border-rose-200 bg-white px-6 py-3 text-sm font-semibold text-rose-700 transition hover:border-rose-300"
          >
            Launch App
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-4 px-6 pb-16 md:grid-cols-2">
        <article className="rounded-2xl border border-rose-100 bg-white/80 p-6">
          <h2 className="text-xl font-semibold">Voice-first interviews</h2>
          <p className="mt-2 text-sm text-slate-600">
            Real-time conversations over LiveKit with STT/TTS, not swipe mechanics.
          </p>
        </article>
        <article className="rounded-2xl border border-rose-100 bg-white/80 p-6">
          <h2 className="text-xl font-semibold">Smart scoring</h2>
          <p className="mt-2 text-sm text-slate-600">
            Effort, creativity, intent clarity, and emotional intelligence scoring with structured feedback.
          </p>
        </article>
        <article className="rounded-2xl border border-rose-100 bg-white/80 p-6">
          <h2 className="text-xl font-semibold">Instant booking</h2>
          <p className="mt-2 text-sm text-slate-600">
            Matched suitors can pick available times immediately through cal.com integration.
          </p>
        </article>
        <article className="rounded-2xl border border-rose-100 bg-white/80 p-6">
          <h2 className="text-xl font-semibold">Operator dashboard</h2>
          <p className="mt-2 text-sm text-slate-600">
            Filter sessions, inspect transcripts, track trends, and pause/resume screening as needed.
          </p>
        </article>
      </section>

      <footer className="mx-auto flex max-w-5xl items-center justify-between px-6 pb-10 text-sm text-slate-500">
        <p>Built with LiveKit, Deepgram, OpenAI, Claude</p>
        <Link to="/privacy" className="underline decoration-rose-300 underline-offset-4">
          Privacy Policy
        </Link>
      </footer>
    </main>
  );
}
