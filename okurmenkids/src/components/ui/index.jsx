import React from 'react';

// ── Button ────────────────────────────────────────────────────────────────────
export const Btn = ({ children, variant = 'primary', size = 'md', onClick, disabled, style, className = '', type = 'button' }) => {
  const variants = {
    primary: { background: 'linear-gradient(135deg, #4ade80, #22c55e)', color: '#0a0f0d', border: 'none' },
    secondary: { background: 'transparent', color: '#4ade80', border: '1px solid rgba(74,222,128,0.3)' },
    ghost: { background: 'rgba(74,222,128,0.08)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.15)' },
    danger: { background: 'linear-gradient(135deg, #fb7185, #f43f5e)', color: '#fff', border: 'none' },
    amber: { background: 'linear-gradient(135deg, #fbbf24, #f59e0b)', color: '#0a0f0d', border: 'none' },
    sky: { background: 'linear-gradient(135deg, #38bdf8, #0ea5e9)', color: '#0a0f0d', border: 'none' },
    violet: { background: 'linear-gradient(135deg, #a78bfa, #7c3aed)', color: '#fff', border: 'none' },
  };
  const sizes = {
    sm: { padding: '6px 14px', fontSize: '13px', borderRadius: '8px' },
    md: { padding: '10px 22px', fontSize: '14px', borderRadius: '10px' },
    lg: { padding: '14px 32px', fontSize: '16px', borderRadius: '12px' },
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={className}
      style={{
        ...variants[variant],
        ...sizes[size],
        fontFamily: 'var(--font-body)',
        fontWeight: 700,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        transition: 'all 0.2s ease',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        ...style,
      }}
      onMouseEnter={e => { if (!disabled) e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.filter = 'brightness(1.1)'; }}
      onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.filter = ''; }}
    >
      {children}
    </button>
  );
};

// ── Card ──────────────────────────────────────────────────────────────────────
export const Card = ({ children, style, onClick, hover = false, glow }) => (
  <div
    onClick={onClick}
    style={{
      background: 'var(--surface)',
      border: `1px solid ${glow ? `rgba(${glow}, 0.3)` : 'var(--border)'}`,
      borderRadius: 'var(--radius)',
      padding: '20px',
      position: 'relative',
      overflow: 'hidden',
      transition: 'all 0.2s ease',
      cursor: onClick ? 'pointer' : undefined,
      boxShadow: glow ? `0 0 30px rgba(${glow}, 0.1)` : undefined,
      ...style,
    }}
    onMouseEnter={e => { if (hover || onClick) { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'rgba(74,222,128,0.3)'; } }}
    onMouseLeave={e => { if (hover || onClick) { e.currentTarget.style.transform = ''; e.currentTarget.style.borderColor = glow ? `rgba(${glow}, 0.3)` : 'var(--border)'; } }}
  >
    {children}
  </div>
);

// ── Badge ─────────────────────────────────────────────────────────────────────
export const Badge = ({ children, color = '#4ade80', bg }) => (
  <span style={{
    display: 'inline-flex',
    alignItems: 'center',
    padding: '3px 10px',
    borderRadius: '20px',
    fontSize: '11px',
    fontWeight: 700,
    letterSpacing: '0.04em',
    background: bg || `rgba(${hexToRgb(color)}, 0.15)`,
    color,
    border: `1px solid rgba(${hexToRgb(color)}, 0.25)`,
  }}>
    {children}
  </span>
);

// ── Progress Bar ──────────────────────────────────────────────────────────────
export const ProgressBar = ({ value, max = 100, color = '#4ade80', height = 6, label }) => (
  <div>
    {label && <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 12, color: 'var(--text2)' }}>
      <span>{label}</span><span>{Math.round((value / max) * 100)}%</span>
    </div>}
    <div style={{ background: 'var(--surface3)', borderRadius: height, height, overflow: 'hidden' }}>
      <div style={{
        width: `${Math.min((value / max) * 100, 100)}%`,
        height: '100%',
        background: `linear-gradient(90deg, ${color}, ${color}cc)`,
        borderRadius: height,
        transition: 'width 0.6s ease',
        boxShadow: `0 0 8px ${color}44`,
      }} />
    </div>
  </div>
);

// ── Input ─────────────────────────────────────────────────────────────────────
export const Input = ({ value, onChange, placeholder, type = 'text', icon, style }) => (
  <div style={{ position: 'relative' }}>
    {icon && <span style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', fontSize: 16, opacity: 0.5 }}>{icon}</span>}
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      style={{
        width: '100%',
        padding: icon ? '12px 16px 12px 44px' : '12px 16px',
        background: 'var(--surface2)',
        border: '1px solid var(--border)',
        borderRadius: 10,
        color: 'var(--text)',
        fontFamily: 'var(--font-body)',
        fontSize: 14,
        outline: 'none',
        transition: 'border-color 0.2s',
        ...style,
      }}
      onFocus={e => e.target.style.borderColor = 'rgba(74,222,128,0.5)'}
      onBlur={e => e.target.style.borderColor = 'var(--border)'}
    />
  </div>
);

// ── Spinner ───────────────────────────────────────────────────────────────────
export const Spinner = ({ size = 24, color = '#4ade80' }) => (
  <div style={{
    width: size, height: size,
    border: `2px solid rgba(${hexToRgb(color)}, 0.2)`,
    borderTopColor: color,
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
    display: 'inline-block',
  }} />
);

// ── Difficulty Badge ──────────────────────────────────────────────────────────
export const DiffBadge = ({ difficulty }) => {
  const map = { easy: ['#4ade80', 'Easy'], medium: ['#fbbf24', 'Medium'], hard: ['#fb7185', 'Hard'] };
  const [color, label] = map[difficulty] || ['#9ab89e', difficulty];
  return <Badge color={color}>{label}</Badge>;
};

// ── Helper ────────────────────────────────────────────────────────────────────
function hexToRgb(hex) {
  if (hex.startsWith('#')) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `${r},${g},${b}`;
  }
  return '74,222,128';
}

// ── Tip Box ───────────────────────────────────────────────────────────────────
export const TipBox = ({ children, icon = '💡', color = '#fbbf24' }) => (
  <div style={{
    background: `rgba(${hexToRgb(color)}, 0.08)`,
    border: `1px solid rgba(${hexToRgb(color)}, 0.2)`,
    borderRadius: 10,
    padding: '12px 16px',
    display: 'flex',
    gap: 10,
    alignItems: 'flex-start',
    fontSize: 13,
    color: 'var(--text2)',
  }}>
    <span style={{ fontSize: 16 }}>{icon}</span>
    <span>{children}</span>
  </div>
);
