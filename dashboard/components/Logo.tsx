export default function Logo() {
  return (
    <span className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-gold/40 bg-gradient-to-br from-gold/25 to-gold/5 shadow-glow transition-shadow group-hover:shadow-glow">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden>
        {/* the eye - بصيرة */}
        <path
          d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"
          stroke="#E7B84E"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <circle cx="12" cy="12" r="3.2" fill="#E7B84E" />
      </svg>
    </span>
  );
}
