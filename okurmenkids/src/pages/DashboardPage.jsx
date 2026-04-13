import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useSessionStore } from '../store/sessionStore';
import { useProgressStore } from '../store/progressStore';
import { Card, ProgressBar, Badge } from '../components/ui';
import { LESSONS, QUESTS } from '../data/content';

const MODULES = [
  {
    path: '/preparation',
    icon: '📖',
    title: 'Preparation',
    subtitle: 'Structured lessons & theory',
    color: '#fb7185',
    gradient: 'linear-gradient(135deg, rgba(251,113,133,0.2), rgba(251,113,133,0.05))',
    border: 'rgba(251,113,133,0.25)',
    tags: ['HTML', 'CSS', 'JavaScript'],
  },
  {
    path: '/quests',
    icon: '⚔️',
    title: 'Play Quests',
    subtitle: 'Learn through mini-games',
    color: '#fbbf24',
    gradient: 'linear-gradient(135deg, rgba(251,191,36,0.2), rgba(251,191,36,0.05))',
    border: 'rgba(251,191,36,0.25)',
    tags: ['Flexbox', 'Typing', 'Logic'],
  },
  {
    path: '/stories',
    icon: '📜',
    title: 'Read Stories',
    subtitle: 'Docs, articles & guides',
    color: '#38bdf8',
    gradient: 'linear-gradient(135deg, rgba(56,189,248,0.2), rgba(56,189,248,0.05))',
    border: 'rgba(56,189,248,0.25)',
    tags: ['Tutorials', 'Concepts', 'Deep dives'],
  },
  {
    path: '/badges',
    icon: '🏅',
    title: 'Earn Badges',
    subtitle: 'Achievements & leaderboard',
    color: '#4ade80',
    gradient: 'linear-gradient(135deg, rgba(74,222,128,0.2), rgba(74,222,128,0.05))',
    border: 'rgba(74,222,128,0.25)',
    tags: ['Badges', 'XP', 'Rankings'],
  },
  {
    path: '/exam',
    icon: '🎓',
    title: 'Take Exam',
    subtitle: 'Session-based assessments',
    color: '#a78bfa',
    gradient: 'linear-gradient(135deg, rgba(167,139,250,0.2), rgba(167,139,250,0.05))',
    border: 'rgba(167,139,250,0.25)',
    tags: ['Quiz', 'Code', 'Graded'],
  },
];

export default function DashboardPage() {
  const nav = useNavigate();
  const { studentName } = useSessionStore();
  const { completedLessons, completedQuests, readStories, badges, xp, level } = useProgressStore();

  const lessonPct = Math.round((completedLessons.length / LESSONS.length) * 100);
  const questPct = Math.round((completedQuests.length / QUESTS.length) * 100);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div style={{ padding: 'clamp(20px, 4vw, 40px)', maxWidth: 1000, margin: '0 auto' }}>

      {/* Hero greeting */}
      <div style={{ marginBottom: 36, animation: 'fadeUp 0.5s ease' }}>
        <div style={{ fontSize: 13, color: 'var(--text3)', marginBottom: 6, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          {greeting()}
        </div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(26px, 4vw, 38px)', fontWeight: 800, color: 'var(--text)', marginBottom: 8 }}>
          {studentName ? `Welcome back, ${studentName}! 👋` : 'Welcome to OkurmenKids! 👋'}
        </h1>
        <p style={{ color: 'var(--text2)', fontSize: 15 }}>
          Ready to level up your coding skills today?
        </p>
      </div>

      {/* XP Stats */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: 14, marginBottom: 36,
      }}>
        {[
          { icon: '⭐', label: 'Total XP', value: xp, color: '#fbbf24' },
          { icon: '🏆', label: 'Level', value: level, color: '#4ade80' },
          { icon: '📖', label: 'Lessons', value: completedLessons.length, color: '#fb7185' },
          { icon: '🏅', label: 'Badges', value: badges.length, color: '#a78bfa' },
        ].map(({ icon, label, value, color }) => (
          <div key={label} style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 14,
            padding: '16px 20px',
            animation: 'fadeUp 0.5s ease',
          }}>
            <div style={{ fontSize: 22, marginBottom: 8 }}>{icon}</div>
            <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
            <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 4, fontWeight: 600 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Progress bars */}
      <Card style={{ marginBottom: 32, padding: '20px 24px' }}>
        <h3 style={{ fontWeight: 700, marginBottom: 16, fontSize: 15, color: 'var(--text)' }}>📊 Your Progress</h3>
        <div style={{ display: 'grid', gap: 14 }}>
          <ProgressBar value={completedLessons.length} max={LESSONS.length} color="#fb7185" label="Lessons completed" />
          <ProgressBar value={completedQuests.length} max={QUESTS.length} color="#fbbf24" label="Quests done" />
          <ProgressBar value={readStories.length} max={4} color="#38bdf8" label="Stories read" />
        </div>
      </Card>

      {/* Module cards */}
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginBottom: 20, color: 'var(--text)' }}>
        Choose your path
      </h2>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 16, marginBottom: 32,
      }}>
        {MODULES.map((m, i) => (
          <div
            key={m.path}
            onClick={() => nav(m.path)}
            style={{
              background: m.gradient,
              border: `1px solid ${m.border}`,
              borderRadius: 16,
              padding: '22px 24px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              animation: `fadeUp ${0.4 + i * 0.07}s ease both`,
              position: 'relative',
              overflow: 'hidden',
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = `0 8px 40px ${m.border}`; }}
            onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}
          >
            <div style={{ fontSize: 34, marginBottom: 12 }}>{m.icon}</div>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: 'var(--text)', marginBottom: 6 }}>{m.title}</h3>
            <p style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 14 }}>{m.subtitle}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {m.tags.map(t => (
                <span key={t} style={{
                  padding: '3px 10px', background: `rgba(0,0,0,0.2)`,
                  color: m.color, borderRadius: 20,
                  fontSize: 11, fontWeight: 700,
                }}>{t}</span>
              ))}
            </div>
            <div style={{ position: 'absolute', bottom: 20, right: 20, fontSize: 24, opacity: 0.3 }}>→</div>
          </div>
        ))}
      </div>

      {/* Recent badges */}
      {badges.length > 0 && (
        <Card style={{ padding: '20px 24px' }}>
          <h3 style={{ fontWeight: 700, marginBottom: 14, fontSize: 15 }}>🏅 Recent Badges</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            {badges.slice(-6).map(b => (
              <div key={b.id} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '8px 14px',
                background: 'var(--surface2)',
                border: `1px solid rgba(${b.color === '#4ade80' ? '74,222,128' : '255,255,255'}, 0.1)`,
                borderRadius: 10,
              }}>
                <span style={{ fontSize: 20 }}>{b.icon}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{b.label}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <style>{`@keyframes fadeUp { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }`}</style>
    </div>
  );
}
