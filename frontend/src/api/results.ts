import { AxiosError } from 'axios';

import { AXIOS_INSTANCE } from './axiosInstance';
import type {
  BookingRequest,
  BookingResponse,
  SlotsResponse,
  VerdictResponse,
} from '../types/results';

export async function getVerdict(sessionId: string): Promise<VerdictResponse> {
  const response = await AXIOS_INSTANCE.get<VerdictResponse>(
    `/api/v1/sessions/${sessionId}/verdict`,
    { validateStatus: (status) => status >= 200 && status < 300 }
  );
  return response.data;
}

export async function getSlots(
  sessionId: string,
  dateFrom?: string,
  dateTo?: string
): Promise<SlotsResponse> {
  const params = new URLSearchParams();
  if (dateFrom) params.set('date_from', dateFrom);
  if (dateTo) params.set('date_to', dateTo);
  const suffix = params.toString() ? `?${params}` : '';
  const response = await AXIOS_INSTANCE.get<SlotsResponse>(
    `/api/v1/sessions/${sessionId}/slots${suffix}`
  );
  return response.data;
}

export async function createBooking(
  sessionId: string,
  data: BookingRequest
): Promise<BookingResponse> {
  const response = await AXIOS_INSTANCE.post<BookingResponse>(
    `/api/v1/sessions/${sessionId}/book`,
    data
  );
  return response.data;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as AxiosError<{ detail?: string; error?: string }>;
    return (
      axiosError.response?.data?.detail ||
      axiosError.response?.data?.error ||
      fallback
    );
  }
  return fallback;
}
