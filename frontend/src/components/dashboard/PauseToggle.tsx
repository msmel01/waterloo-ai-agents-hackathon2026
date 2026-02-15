type Props = {
  active: boolean;
  isLoading?: boolean;
  onToggle: (next: boolean) => void;
};

export function PauseToggle({ active, isLoading, onToggle }: Props) {
  return (
    <button
      type="button"
      disabled={isLoading}
      onClick={() => onToggle(!active)}
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium ${
        active
          ? 'border-green-300 bg-green-50 text-green-700'
          : 'border-amber-300 bg-amber-50 text-amber-700'
      } ${isLoading ? 'opacity-70' : ''}`}
    >
      <span className={`h-2.5 w-2.5 rounded-full ${active ? 'bg-green-500' : 'bg-amber-500'}`} />
      {active ? 'Active' : 'Paused'}
    </button>
  );
}
