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

export function Window({ title, icon, children }: WindowProps) {
  const Icon = icons[icon];

  return (
    <div
      className="border-2 border-win-border overflow-hidden"
      style={{ boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}
    >
      {/* Title bar - raised bevel */}
      <div
        className="flex items-center gap-2 bg-win-titlebar px-2 py-1.5 text-white"
        style={{
          boxShadow:
            'inset 2px 2px 0 rgba(255,255,255,0.2), inset -2px -2px 0 rgba(0,0,0,0.2), 0 2px 0 rgba(0,0,0,0.2)',
        }}
      >
        <Icon />
        <span className="flex-1 text-sm font-medium text-white truncate">{title}</span>
        <div className="flex gap-1">
          <button type="button" className="w-4 h-4 border border-win-titlebarLight flex items-center justify-center" aria-label="Minimize">
            <span className="text-win-titlebarLight text-[10px] leading-none">−</span>
          </button>
          <button type="button" className="w-4 h-4 border border-win-titlebarLight flex items-center justify-center" aria-label="Maximize">
            <span className="text-win-titlebarLight text-[10px] leading-none">□</span>
          </button>
          <button type="button" className="w-4 h-4 border border-win-titlebarLight flex items-center justify-center" aria-label="Close">
            <span className="text-win-titlebarLight text-[10px] leading-none">×</span>
          </button>
        </div>
      </div>
      {/* Content - recessed bevel */}
      <div
        className="p-4 bg-win-content"
        style={{
          boxShadow: 'inset 3px 3px 0 rgba(255,255,255,0.12), inset -3px -3px 0 rgba(0,0,0,0.35)',
        }}
      >
        {children}
      </div>
    </div>
  );
}
