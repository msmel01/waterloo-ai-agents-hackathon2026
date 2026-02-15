import { Navigate, useParams } from 'react-router-dom';

export function InterviewCompleteScreen() {
  const { sessionId = '' } = useParams<{ sessionId: string }>();
  return <Navigate to={`/session/${sessionId}/results`} replace />;
}
