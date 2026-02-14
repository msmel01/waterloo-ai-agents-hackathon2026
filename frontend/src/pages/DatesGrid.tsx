import { Link } from 'react-router-dom';
import { Window } from '../components/Window';
import { PLACEHOLDER_DATES } from '../data/placeholders';

export function DatesGrid() {
  return (
    <div className="min-h-screen bg-win-bg flex flex-col py-6 px-4">
      <header className="w-full max-w-4xl mx-auto mb-6">
        <h1 className="text-win-textMuted text-sm font-medium uppercase tracking-wider">
          Valentine Hotline
        </h1>
        <div className="h-px bg-win-border mt-1" />
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full">
        <Window title="CoffeeDates.exe" icon="person">
          <h2 className="text-win-text text-lg font-semibold mb-4">Your Coffee Dates</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {PLACEHOLDER_DATES.map((date) => (
              <Link
                key={date.id}
                to={`/profile/${date.slug}`}
                className="block border border-win-border bg-win-bg p-4 hover:border-win-titlebar transition-colors"
              >
                <div className="aspect-square max-w-[80px] mx-auto mb-3 border border-win-border flex items-center justify-center bg-win-content">
                  <span className="text-win-titlebar text-2xl font-bold">{date.name[0]}</span>
                </div>
                <h3 className="text-win-text text-sm font-medium text-center">{date.name}</h3>
                <p className="text-win-textMuted text-xs text-center mt-1">View profile →</p>
              </Link>
            ))}
          </div>
        </Window>
      </main>
    </div>
  );
}
