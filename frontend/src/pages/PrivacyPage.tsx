import { Link } from 'react-router-dom';

export function PrivacyPage() {
  return (
    <main className="min-h-screen bg-slate-50 px-4 py-10">
      <article className="mx-auto max-w-3xl rounded-2xl border border-slate-200 bg-white p-8">
        <h1 className="text-3xl font-bold text-slate-900">Privacy Policy</h1>
        <p className="mt-4 text-sm text-slate-600">
          Valentine Hotline collects only what is needed to run AI screening and optional date booking.
        </p>

        <section className="mt-6 space-y-2 text-sm text-slate-700">
          <h2 className="text-lg font-semibold text-slate-900">What we collect</h2>
          <p>Name, profile details, voice transcript, session metadata, and booking email for successful matches.</p>
          <h2 className="text-lg font-semibold text-slate-900">How we use it</h2>
          <p>We evaluate responses, generate scores/feedback, and support booking workflows.</p>
          <h2 className="text-lg font-semibold text-slate-900">Who can access it</h2>
          <p>The Heart can view transcript and scoring details in the dashboard.</p>
          <h2 className="text-lg font-semibold text-slate-900">Retention</h2>
          <p>Data is retained for up to 90 days by default and then anonymized based on system policy.</p>
          <h2 className="text-lg font-semibold text-slate-900">Third-party processors</h2>
          <p>LiveKit, Deepgram, OpenAI, Anthropic, and cal.com process data to provide service features.</p>
          <h2 className="text-lg font-semibold text-slate-900">Data requests</h2>
          <p>Contact the project operator to request deletion or correction.</p>
        </section>

        <Link to="/" className="mt-8 inline-block text-sm font-medium text-rose-700 underline">
          Back to Valentine Hotline
        </Link>
      </article>
    </main>
  );
}
