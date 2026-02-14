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

/** Palette: Lavender Purple (heading), Orchid Mist / Pink Carnation (bevel), Desert Sand (fill) */
const DARK_PURPLE = '#905ACA'; // title bar - Lavender Purple
const LIGHT_PURPLE = '#C566C2'; // border/bevel base - Orchid Mist
const LIGHT_PURPLE_HIGHLIGHT = '#F487B8'; // top/left of raised bevel - Pink Carnation
const LIGHT_PURPLE_SHADOW = '#905ACA'; // bottom/right of raised bevel - Lavender
const INNER_FILL = '#F5E7F0'; // Desert Sand

export function Window({ title, icon, children }: WindowProps) {
  const Icon = icons[icon];

  return (
    <div
      className="overflow-hidden flex flex-col min-h-0"
      style={{
        borderTop: `2px solid ${LIGHT_PURPLE_HIGHLIGHT}`,
        borderLeft: `2px solid ${LIGHT_PURPLE_HIGHLIGHT}`,
        borderRight: `2px solid ${LIGHT_PURPLE_SHADOW}`,
        borderBottom: `2px solid ${LIGHT_PURPLE_SHADOW}`,
      }}
    >
      {/* Title bar - darker purple, raised */}
      <div
        className="flex items-center gap-2 px-2 py-1.5 text-white flex-shrink-0"
        style={{
          backgroundColor: DARK_PURPLE,
          boxShadow: `inset 1px 1px 0 rgba(255,255,255,0.2), 0 1px 0 ${LIGHT_PURPLE_SHADOW}`,
        }}
      >
        <Icon />
        <span className="flex-1 text-sm font-medium text-center truncate">{title}</span>
        <div className="flex gap-0.5">
          {(['−', '□', '×'] as const).map((symbol, i) => (
            <button
              key={symbol}
              type="button"
              className="w-5 h-5 flex items-center justify-center"
              style={{
                backgroundColor: DARK_PURPLE,
                border: `1px solid ${LIGHT_PURPLE}`,
                boxShadow: `inset 1px 1px 0 ${LIGHT_PURPLE_HIGHLIGHT}, inset -1px -1px 0 ${LIGHT_PURPLE_SHADOW}`,
                fontSize: '10px',
                lineHeight: 1,
                color: 'rgba(255,255,255,0.95)',
              }}
              aria-label={i === 0 ? 'Minimize' : i === 1 ? 'Maximize' : 'Close'}
            >
              {symbol}
            </button>
          ))}
        </div>
      </div>
      {/* Content - Desert Sand inner fill, recessed with palette bevel */}
      <div
        className="p-4 text-gray-900 flex-1 min-h-0"
        style={{
          backgroundColor: INNER_FILL,
          borderTop: `2px solid ${LIGHT_PURPLE_SHADOW}`,
          borderLeft: `2px solid ${LIGHT_PURPLE_SHADOW}`,
          borderRight: `2px solid ${LIGHT_PURPLE_HIGHLIGHT}`,
          borderBottom: `2px solid ${LIGHT_PURPLE_HIGHLIGHT}`,
          boxShadow: `inset 2px 2px 0 ${LIGHT_PURPLE_SHADOW}, inset -2px -2px 0 ${LIGHT_PURPLE_HIGHLIGHT}`,
        }}
      >
        {children}
      </div>
    </div>
  );
}
