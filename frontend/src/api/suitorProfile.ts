/**
 * Stub for syncing suitor profile data (gender, orientation, age) to backend.
 * Not sent to Clerk — stored locally for now; wire to your backend when ready.
 */
export interface SuitorProfileData {
  gender: string;
  orientation: string;
  age: string;
}

export async function syncSuitorProfile(data: SuitorProfileData): Promise<void> {
  // Stub: store in localStorage for now; replace with API call when backend exists.
  localStorage.setItem('suitor_gender', data.gender);
  localStorage.setItem('suitor_orientation', data.orientation);
  localStorage.setItem('suitor_age', data.age);
}
