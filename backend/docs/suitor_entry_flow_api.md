# Suitor Entry Flow API

1. `GET /api/v1/public/{slug}`
- Returns public Heart landing data:
`display_name`, `bio`, `photo_url`, `agent_ready`, `has_calendar`, `question_count`, `estimated_duration`, `persona_preview`, `is_accepting`.

2. Clerk auth on frontend
- Clerk handles login/signup and webhook syncs Suitor record.

3. `POST /api/v1/suitors/register`
- Completes/updates Suitor profile (`name`, `age`, `gender`, `orientation`, `intro_message`).

4. `GET /api/v1/sessions/pre-check`
- Returns `can_start`, `reason`, profile/heart readiness, remaining daily quota, and `active_session_id` if reconnect is needed.

5. `POST /api/v1/sessions/start`
- Creates or reconnects to a session.
- Returns `session_id`, `livekit_url`, `livekit_token`, `room_name`, `status` (`ready` or `reconnecting`), `message`.

6. Live interview over LiveKit
- Realtime voice flow is handled by LiveKit + agent worker.

7. `GET /api/v1/sessions/{id}/status`
- Polls lifecycle state, includes `end_reason`, duration, question progress, and verdict pipeline (`has_verdict`, `verdict_status`).

8. `GET /api/v1/suitors/me/sessions`
- Returns recent session history and remaining daily quota.
