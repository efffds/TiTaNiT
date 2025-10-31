export default function LogoTiTi({ size = 140 }) {
  const w = size;
  const h = Math.round(size * 0.58);
  return (
    <svg
      width={w}
      height={h}
      viewBox="0 0 350 200"
      className="brand-svg"
      role="img"
      aria-label="TiTi logo"
    >
      {/* centered group */}
      <g transform="translate(0,0)">
        {/* left heart blob */}
        <path d="M90 90c-25-18-25-49 1-58 15-5 30 3 36 15 6-12 21-20 36-15 26 9 26 40 1 58-14 10-26 17-37 23-11-6-23-13-37-23z" fill="#26de50"/>
        {/* right heart blob (mirrored composition) */}
        <path d="M260 90c-25-18-25-49 1-58 15-5 30 3 36 15 6-12 21-20 36-15 26 9 26 40 1 58-14 10-26 17-37 23-11-6-23-13-37-23z" fill="#26de50"/>
        {/* wordmark centered */}
        <g fill="#ffffff" fontFamily="Manrope, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif" fontWeight="900">
          <text x="50%" y="105" textAnchor="middle" fontSize="88" letterSpacing="2">TiTi</text>
          <text x="50%" y="135" textAnchor="middle" fontSize="20" opacity="0.9">for TITANIT</text>
        </g>
      </g>
    </svg>
  );
}
