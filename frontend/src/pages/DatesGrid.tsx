import { Link } from 'react-router-dom';
import { Window } from '../components/Window';
import { PLACEHOLDER_DATES } from '../data/placeholders';

export function DatesGrid() {
  return (
    <div className="min-h-screen bg-win-bg flex flex-col py-6 px-4">
      <header className="w-full max-w-5xl mx-auto mb-6">
        <h1 className="text-win-textMuted text-sm font-medium uppercase tracking-wider">
          Valentine Hotline
        </h1>
        <div className="h-px bg-win-border mt-1" />
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full">
        <h2 className="text-win-text text-lg font-semibold mb-4">Your Coffee Dates</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {PLACEHOLDER_DATES.map((date) => (
            <Link key={date.id} to={`/profile/${date.slug}`} className="block">
              <Window title={`${date.name}.exe`} icon="person">
                <div className="flex flex-col items-center">
                  <div className="aspect-square w-20 h-20 border border-win-border flex items-center justify-center bg-win-bg mb-3">
                    <span className="text-win-titlebar text-2xl font-bold">{date.name[0]}</span>
                  </div>
                  <h3 className="text-win-text text-sm font-medium text-center">{date.name}</h3>
                  <p className="text-win-textMuted text-xs text-center mt-1">View profile →</p>
                </div>
              </Window>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
