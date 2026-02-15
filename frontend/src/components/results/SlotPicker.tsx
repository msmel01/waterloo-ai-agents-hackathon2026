import { useMemo, useState } from 'react';
import { toast } from 'sonner';

import { getApiErrorMessage } from '../../api/results';
import { useBooking } from '../../hooks/useBooking';
import { useSlots } from '../../hooks/useSlots';
import type { BookingResponse } from '../../types/results';

interface SlotPickerProps {
  sessionId: string;
  suitorName: string;
  enabled: boolean;
  onBooked: (booking: BookingResponse, email: string) => void;
}

export function SlotPicker({ sessionId, suitorName, enabled, onBooked }: SlotPickerProps) {
  const [selectedStart, setSelectedStart] = useState<string | null>(null);
  const [email, setEmail] = useState('');
  const [notes, setNotes] = useState('');

  const slotsQuery = useSlots(sessionId, enabled);
  const bookingMutation = useBooking(sessionId);

  const selectedSlot = useMemo(() => {
    const days = slotsQuery.data?.slots ?? [];
    for (const day of days) {
      const slot = day.times.find((t) => t.start === selectedStart);
      if (slot) {
        return slot;
      }
    }
    return null;
  }, [slotsQuery.data?.slots, selectedStart]);

  const handleConfirm = async () => {
    if (!selectedStart || !email.trim()) {
      toast.error('Choose a slot and provide your email.');
      return;
    }

    try {
      const booking = await bookingMutation.mutateAsync({
        slot_start: selectedStart,
        suitor_name: suitorName,
        suitor_email: email.trim(),
        suitor_notes: notes.trim() || undefined,
      });
      onBooked(booking, email.trim());
      toast.success(booking.message || 'Date booked!');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not book this slot. Please try another.'));
      slotsQuery.refetch();
    }
  };

  if (!enabled) {
    return null;
  }

  if (slotsQuery.isLoading) {
    return <section className="m6-card text-rose-100 text-sm">Loading available slots…</section>;
  }

  if (slotsQuery.isError) {
    return (
      <section className="m6-card space-y-2">
        <p className="text-rose-100 text-sm">Unable to fetch availability right now.</p>
        <button
          type="button"
          onClick={() => slotsQuery.refetch()}
          className="px-3 py-2 rounded border border-white/30 text-white text-sm"
        >
          Retry
        </button>
      </section>
    );
  }

  return (
    <section className="m6-card space-y-4">
      <h3 className="text-lg font-semibold text-white">📅 Book Your Date</h3>
      <div className="space-y-3">
        {slotsQuery.data?.slots.map((day) => (
          <div key={day.date}>
            <p className="text-rose-200 text-sm mb-2">{day.day_label}</p>
            <div className="flex flex-wrap gap-2">
              {day.times.map((slot) => {
                const selected = selectedStart === slot.start;
                return (
                  <button
                    key={slot.start}
                    type="button"
                    onClick={() => setSelectedStart(slot.start)}
                    className={`min-h-11 px-3 rounded-full border text-sm ${
                      selected
                        ? 'bg-green-500/80 border-green-200 text-white'
                        : 'bg-white/10 border-white/30 text-rose-50 hover:bg-white/20'
                    }`}
                  >
                    {slot.display}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="space-y-3">
        <input
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          type="email"
          placeholder="Your email"
          className="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white placeholder:text-rose-200"
        />
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Optional note"
          className="w-full rounded border border-white/30 bg-white/10 px-3 py-2 text-white placeholder:text-rose-200"
          rows={3}
        />
      </div>

      <button
        type="button"
        onClick={handleConfirm}
        disabled={bookingMutation.isPending || !selectedSlot}
        className="w-full min-h-11 rounded bg-green-500 text-white font-semibold disabled:opacity-60"
      >
        {bookingMutation.isPending ? 'Booking…' : '💚 Confirm Date'}
      </button>
    </section>
  );
}
