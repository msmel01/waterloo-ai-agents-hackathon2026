import { Link } from 'react-router-dom';

import type { BookingResponse } from '../../types/results';
import { ShareCard } from './ShareCard';

interface BookingConfirmationProps {
  booking: BookingResponse;
  email: string;
  score: number;
}

export function BookingConfirmation({ booking, email, score }: BookingConfirmationProps) {
  return (
    <section className="m6-card m6-card-date space-y-4">
      <h3 className="text-2xl font-bold text-white">💚 IT'S OFFICIAL!</h3>
      <p className="text-rose-50 text-sm">Your date is booked.</p>
      <div className="bg-white/10 border border-white/20 rounded p-3 text-rose-50 text-sm">
        <p>{booking.slot.display}</p>
        <p className="opacity-80">Confirmation sent to {email}</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <ShareCard verdict="date" score={score} />
        <Link
          to="/chats"
          className="px-4 py-2 rounded border border-white/30 text-white text-sm hover:bg-white/10"
        >
          🏠 Back to Home
        </Link>
      </div>
    </section>
  );
}
