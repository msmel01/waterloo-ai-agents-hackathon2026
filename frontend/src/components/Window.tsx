import type { ReactNode } from 'react';

interface WindowProps {
  title: string;
  icon: 'phone' | 'person' | 'info';
  children: ReactNode;
}

const PhoneIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
    <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z" />
  </svg>
);

const PersonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
    <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);

const InfoIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
    <circle cx="12" cy="12" r="10" />
    <path d="M12 16v-4M12 8h.01" />
  </svg>
);

const icons = { phone: PhoneIcon, person: PersonIcon, info: InfoIcon };

/** Multi-layer 3D outer frame: light top/left, dark bottom/right */
const OUTER_BEVEL =
  'inset 1px 1px 0 rgba(255,255,255,0.12), inset 2px 2px 0 rgba(255,255,255,0.06), inset -1px -1px 0 rgba(0,0,0,0.4), inset -2px -2px 0 rgba(0,0,0,0.25), 0 4px 12px rgba(0,0,0,0.2)';

export function Window({ title, icon, children }: WindowProps) {
  const Icon = icons[icon];

  return (
    <div
      className="overflow-hidden flex flex-col min-h-0"
      style={{
        border: '2px solid',
        borderColor: '#2D1B4E',
        boxShadow: OUTER_BEVEL,
      }}
    >
      {/* Title bar - solid color, raised */}
      <div
        className="flex items-center gap-2 px-2 py-1.5 text-white flex-shrink-0"
        style={{
          backgroundColor: '#8301E1',
          boxShadow:
            'inset 2px 2px 0 rgba(255,255,255,0.15), inset -1px -1px 0 rgba(0,0,0,0.2), 0 1px 0 rgba(0,0,0,0.15)',
        }}
      >
        <Icon />
        <span className="flex-1 text-sm font-medium text-center truncate">{title}</span>
        <div className="flex gap-0.5">
          {(['−', '□', '×'] as const).map((symbol, i) => (
            <button
              key={symbol}
              type="button"
              className="w-5 h-5 flex items-center justify-center border border-win-titlebarLight"
              style={{
                backgroundColor: '#8301E1',
                boxShadow: 'inset 1px 1px 0 rgba(255,255,255,0.2), inset -1px -1px 0 rgba(0,0,0,0.3)',
                fontSize: '10px',
                lineHeight: 1,
                color: 'rgba(255,255,255,0.9)',
              }}
              aria-label={i === 0 ? 'Minimize' : i === 1 ? 'Maximize' : 'Close'}
            >
              {symbol}
            </button>
          ))}
        </div>
      </div>
      {/* Content - recessed white inset (retro style), fills remaining space */}
      <div
        className="p-4 text-gray-900 flex-1 min-h-0"
        style={{
          backgroundColor: '#f5f5f5',
          boxShadow:
            'inset 2px 2px 0 rgba(0,0,0,0.1), inset -1px -1px 0 rgba(255,255,255,0.8)',
          borderTop: '1px solid rgba(0,0,0,0.12)',
        }}
      >
        {children}
      </div>
    </div>
  );
}
