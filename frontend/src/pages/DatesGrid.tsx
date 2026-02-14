import { Link } from 'react-router-dom';

import { PLACEHOLDER_DATES } from '../data/placeholders';

export function DatesGrid() {
  return (
    <div className="min-h-screen bg-y2k flex flex-col relative">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <span className="absolute top-24 left-[10%] text-y2k-hotpink/30 text-xl">✦</span>
        <span className="absolute top-40 right-[12%] text-y2k-cyan/40 text-2xl">⋆</span>
      </div>

      <header
        className="flex items-center justify-center px-4 py-5 border-b-4 border-y2k-hotpink relative z-10"
        style={{ boxShadow: '0 4px 0 rgba(255,20,147,0.3)' }}
      >
        <h1 className="font-rochester text-4xl text-y2k-hotpink text-glow-pink">
          Valentine Hotline
        </h1>
      </header>

      <main className="flex-1 p-6 relative z-10">
        <h2 className="font-rochester text-3xl text-y2k-cyan mb-6 text-center">
          Your Coffee Dates
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {PLACEHOLDER_DATES.map((date) => (
            <Link
              key={date.id}
              to={`/profile/${date.slug}`}
              className="block border-4 border-y2k-hotpink bg-black/60 p-6 hover:shadow-neon-pink transition-all group"
              style={{ boxShadow: '0 0 15px rgba(255,20,147,0.2)' }}
            >
              <div className="aspect-square bg-y2k-purple/20 border-2 border-y2k-cyan/50 flex items-center justify-center mb-4 group-hover:border-y2k-hotpink transition-colors">
                <span className="font-rochester text-4xl text-y2k-hotpink">{date.name[0]}</span>
              </div>
              <h3 className="font-rochester text-2xl text-y2k-cyan text-center">{date.name}</h3>
              <p className="font-pixel text-sm text-y2k-cyan/70 text-center mt-1">View profile →</p>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
