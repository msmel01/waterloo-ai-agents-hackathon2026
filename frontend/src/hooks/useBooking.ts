import { useMutation } from '@tanstack/react-query';

import { createBooking } from '../api/results';
import type { BookingRequest } from '../types/results';

export function useBooking(sessionId: string) {
  return useMutation({
    mutationKey: ['book-slot', sessionId],
    mutationFn: (payload: BookingRequest) => createBooking(sessionId, payload),
  });
}
