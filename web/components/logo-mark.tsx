/**
 * Promptcha belgisi — serif «P» (wordmark Instrument Serif bilan bir uslubda).
 * Shakl `app/icon.svg` (favicon) bilan bir xil; oʻzgartirilsa ikkalasi ham yangilanadi.
 */
export function LogoMark({
  size = 24,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 32 32"
      width={size}
      height={size}
      className={className}
      aria-hidden
      focusable="false"
    >
      <rect width="32" height="32" rx="7" fill="var(--accent)" />
      <g stroke="var(--on-accent)" fill="none" strokeWidth="4.3">
        <path d="M12.9 6.9V25.1" />
        <path d="M12.9 9.05h3.6a4.6 4.6 0 0 1 0 9.2h-3.6" />
      </g>
      <rect
        x="8.2"
        y="22.95"
        width="9.4"
        height="2.15"
        rx="0.8"
        fill="var(--on-accent)"
      />
    </svg>
  );
}
