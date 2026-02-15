import { toast } from 'sonner';

import type { VerdictValue } from '../../types/results';

interface ShareCardProps {
  verdict: VerdictValue;
  score: number;
}

export function ShareCard({ verdict, score }: ShareCardProps) {
  const handleShare = async () => {
    const text =
      verdict === 'date'
        ? `I got a DATE on Valentine Hotline! 💚 Score: ${Math.round(score)}/100`
        : `I tried Valentine Hotline! 💜 Score: ${Math.round(score)}/100`;

    try {
      if (navigator.share) {
        await navigator.share({
          title: 'Valentine Hotline',
          text,
          url: window.location.href,
        });
      } else {
        await navigator.clipboard.writeText(`${text}\n${window.location.href}`);
        toast.success('Share text copied to clipboard.');
      }
    } catch {
      toast.error('Unable to share right now.');
    }
  };

  return (
    <button
      type="button"
      onClick={handleShare}
      className="px-4 py-2 rounded border border-white/30 text-white text-sm hover:bg-white/10"
    >
      📤 Share Your Result
    </button>
  );
}
