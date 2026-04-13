import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSessionStore } from '../store/sessionStore';
import { useProgressStore } from '../store/progressStore';

const NAV = [
  { path: '/dashboard', icon: '⬡', label: 'Home' },
  { path: '/preparation', icon: '📖', label: 'Learn' },
  { path: '/quests', icon: '⚔️', label: 'Quests' },
  { path: '/stories', icon: '📜', label: 'Stories' },
  { path: '/badges', icon: '🏅', label: 'Badges' },
  { path: '/exam', icon: '🎓', label: 'Exam' },
];

export default function Navbar() {
  const nav = useNavigate();
  const loc = useLocation();
  const { studentName } = useSessionStore();
  const { xp, level } = useProgressStore();
  const [menuOpen, setMenuOpen] = useState(false);

  const isActive = (path) => loc.pathname.startsWith(path);

  return (
    <>
      {/* Desktop sidebar */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, bottom: 0, width: 220,
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column',
        padding: '24px 16px',
        zIndex: 100,
        transition: 'all 0.3s ease',
      }} className="desktop-nav">
        {/* Logo */}
        <div style={{ marginBottom: 32, cursor: 'pointer' }} onClick={() => nav('/dashboard')}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 38, height: 38,
              background: 'linear-gradient(135deg, #4ade80, #22c55e)',
              borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 18, boxShadow: '0 0 20px rgba(74,222,128,0.3)',
            }}>🦉</div>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 15, color: 'var(--green)' }}>Okurmen</div>
              <div style={{ fontSize: 10, color: 'var(--text3)', fontWeight: 600, letterSpacing: '0.1em' }}>KIDS</div>
            </div>
          </div>
        </div>

        {/* Nav links */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {NAV.map(({ path, icon, label }) => (
            <button key={path} onClick={() => nav(path)} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 14px', borderRadius: 10,
              background: isActive(path) ? 'var(--green-dim)' : 'transparent',
              border: isActive(path) ? '1px solid rgba(74,222,128,0.2)' : '1px solid transparent',
              color: isActive(path) ? 'var(--green)' : 'var(--text2)',
              fontSize: 14, fontWeight: isActive(path) ? 700 : 500,
              cursor: 'pointer', textAlign: 'left', width: '100%',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { if (!isActive(path)) { e.currentTarget.style.background = 'var(--surface2)'; e.currentTarget.style.color = 'var(--text)'; } }}
            onMouseLeave={e => { if (!isActive(path)) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text2)'; } }}>
              <span style={{ fontSize: 18 }}>{icon}</span>
              {label}
            </button>
          ))}
        </div>

        {/* User info */}
        {studentName && (
          <div style={{
            marginTop: 'auto', padding: '12px 14px',
            background: 'var(--surface2)', borderRadius: 10,
            border: '1px solid var(--border)',
          }}>
            <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.08em' }}>You</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)', marginBottom: 6 }}>{studentName}</div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 12, color: 'var(--green)' }}>⭐ {xp} XP</span>
              <span style={{
                background: 'var(--green-dim)', color: 'var(--green)',
                border: '1px solid rgba(74,222,128,0.2)',
                padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 700,
              }}>Lv {level}</span>
            </div>
          </div>
        )}
      </nav>

      {/* Mobile top bar */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, height: 56,
        background: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 16px',
        zIndex: 100,
      }} className="mobile-nav">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }} onClick={() => nav('/dashboard')}>
          <span style={{ fontSize: 24 }}>🦉</span>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, color: 'var(--green)', fontSize: 16 }}>OkurmenKids</span>
        </div>
        <button onClick={() => setMenuOpen(!menuOpen)} style={{ background: 'none', border: 'none', color: 'var(--text)', fontSize: 20 }}>
          {menuOpen ? '✕' : '☰'}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div style={{
          position: 'fixed', top: 56, left: 0, right: 0, bottom: 0,
          background: 'var(--bg)',
          zIndex: 99,
          padding: '16px',
          display: 'flex', flexDirection: 'column', gap: 8,
        }}>
          {NAV.map(({ path, icon, label }) => (
            <button key={path} onClick={() => { nav(path); setMenuOpen(false); }} style={{
              display: 'flex', alignItems: 'center', gap: 14,
              padding: '14px 16px', borderRadius: 12,
              background: isActive(path) ? 'var(--green-dim)' : 'var(--surface)',
              border: `1px solid ${isActive(path) ? 'rgba(74,222,128,0.2)' : 'var(--border)'}`,
              color: isActive(path) ? 'var(--green)' : 'var(--text)',
              fontSize: 16, fontWeight: 600, cursor: 'pointer', textAlign: 'left', width: '100%',
            }}>
              <span style={{ fontSize: 22 }}>{icon}</span>
              {label}
            </button>
          ))}
        </div>
      )}

      <style>{`
        @media (min-width: 768px) { .mobile-nav { display: none !important; } }
        @media (max-width: 767px) { .desktop-nav { display: none !important; } }
      `}</style>
    </>
  );
}
