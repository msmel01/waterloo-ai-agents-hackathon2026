type Props = {
  page: number;
  totalPages: number;
  hasPrev: boolean;
  hasNext: boolean;
  onChange: (page: number) => void;
};

export function Pagination({ page, totalPages, hasPrev, hasNext, onChange }: Props) {
  return (
    <div className="mt-4 flex items-center justify-center gap-3 text-sm">
      <button
        type="button"
        disabled={!hasPrev}
        className="rounded border border-slate-300 px-3 py-1 disabled:opacity-50"
        onClick={() => onChange(page - 1)}
      >
        Prev
      </button>
      <span className="text-slate-600">
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        disabled={!hasNext}
        className="rounded border border-slate-300 px-3 py-1 disabled:opacity-50"
        onClick={() => onChange(page + 1)}
      >
        Next
      </button>
    </div>
  );
}
