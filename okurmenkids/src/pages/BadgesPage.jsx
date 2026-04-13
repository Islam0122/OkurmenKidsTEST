import React from 'react';
import { useProgressStore } from '../store/progressStore';
import { useSessionStore } from '../store/sessionStore';
import { Card, ProgressBar } from '../components/ui';
import { LEADERBOARD, LESSONS, QUESTS } from '../data/content';

const ALL_BADGES = [
  { id: 'first_lesson', label: 'First Steps', icon: '🌱', desc: 'Complete your first lesson', color: '#4ade80', req: 'Complete 1 lesson' },
  { id: 'lesson_5', label: 'Scholar', icon: '📚', desc: 'Complete 5 lessons', color: '#38bdf8', req: 'Complete 5 lessons' },
  { id: 'first_quest', label: 'Quest Starter', icon: '⚔️', desc: 'Complete your first quest', color: '#fbbf24', req: 'Complete 1 quest' },
  { id: 'quest_master', label: 'Quest Master', icon: '🏆', desc: 'Complete 5 quests', color: '#a78bfa', req: 'Complete 5 quests' },
  { id: 'reader', label: 'Book Worm', icon: '🐛', desc: 'Read 3 stories', color: '#fb7185', req: 'Read 3 stories' },
  { id: 'xp_100', label: 'Rising Star', icon: '⭐', desc: 'Earn 100 XP', color: '#fbbf24', req: 'Earn 100 XP' },
  { id: 'xp_500', label: 'Code Wizard', icon: '🧙', desc: 'Earn 500 XP', color: '#a78bfa', req: 'Earn 500 XP' },
];

export default function BadgesPage() {
  const { badges, xp, level, completedLessons, completedQuests, readStories, scores } = useProgressStore();
  const { studentName } = useSessionStore();

  const earnedIds = new Set(badges.map(b => b.id));
  const nextLevel = (level) * 100;
  const currentLevelXp = xp - (level - 1) * 100;

  // Build leaderboard with user
  const userEntry = { rank: '?', name: studentName || 'You', xp, badge: '🎓', level, isYou: true };
  const lb = [...LEADERBOARD];
  // Insert user at correct position
  const userRank = lb.filter(e => e.xp > xp).length + 1;
  userEntry.rank = userRank;

  const topBestScore = Object.entries(scores).sort((a, b) => b[1] - a[1]).slice(0, 3);

  return (
    <div style={{ padding: 'clamp(16px,4vw,40px)', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: 12, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Module 4</div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(24px,4vw,36px)', fontWeight: 800, color: 'var(--text)', marginBottom: 10 }}>🏅 Earn Badges</h1>
        <p style={{ color: 'var(--text2)', fontSize: 15 }}>Achievements, rankings, and your journey</p>
      </div>

      {/* User stats hero */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(74,222,128,0.15), rgba(74,222,128,0.03))',
        border: '1px solid rgba(74,222,128,0.2)',
        borderRadius: 20, padding: '24px 28px',
        marginBottom: 32,
        display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap',
        boxShadow: '0 0 40px rgba(74,222,128,0.08)',
      }}>
        <div style={{ fontSize: 64 }}>🦉</div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 800, color: 'var(--text)', marginBottom: 4 }}>{studentName || 'Coder'}</div>
          <div style={{ color: 'var(--text3)', fontSize: 13, marginBottom: 12 }}>Level {level} · {xp} XP total</div>
          <ProgressBar value={currentLevelXp} max={100} color="#4ade80" label={`Progress to Level ${level + 1}`} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[
            { icon: '📖', value: completedLessons.length, label: 'Lessons' },
            { icon: '⚔️', value: completedQuests.length, label: 'Quests' },
            { icon: '📜', value: readStories.length, label: 'Stories' },
            { icon: '🏅', value: badges.length, label: 'Badges' },
          ].map(({ icon, value, label }) => (
            <div key={label} style={{ textAlign: 'center', background: 'rgba(0,0,0,0.2)', borderRadius: 10, padding: '10px 16px' }}>
              <div style={{ fontSize: 16 }}>{icon}</div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 800, color: '#4ade80' }}>{value}</div>
              <div style={{ fontSize: 11, color: 'var(--text3)', fontWeight: 600 }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Badges grid */}
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginBottom: 16, color: 'var(--text)' }}>Your Badges</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14, marginBottom: 36 }}>
        {ALL_BADGES.map((b, i) => {
          const earned = earnedIds.has(b.id);
          const earnedData = badges.find(eb => eb.id === b.id);
          return (
            <div key={b.id} style={{
              background: earned ? `rgba(${b.color === '#4ade80' ? '74,222,128' : b.color === '#38bdf8' ? '56,189,248' : b.color === '#fbbf24' ? '251,191,36' : b.color === '#a78bfa' ? '167,139,250' : '251,113,133'},0.1)` : 'var(--surface)',
              border: `1px solid ${earned ? b.color + '44' : 'var(--border)'}`,
              borderRadius: 14, padding: '20px 18px',
              textAlign: 'center', opacity: earned ? 1 : 0.5,
              animation: `fadeUp ${0.3 + i * 0.06}s ease both`,
              transition: 'all 0.2s',
              filter: earned ? 'none' : 'grayscale(1)',
            }}>
              <div style={{ fontSize: 40, marginBottom: 10, filter: earned ? 'none' : 'grayscale(1)' }}>{b.icon}</div>
              <div style={{ fontWeight: 700, fontSize: 14, color: earned ? 'var(--text)' : 'var(--text3)', marginBottom: 6 }}>{b.label}</div>
              <div style={{ fontSize: 12, color: 'var(--text3)', lineHeight: 1.4 }}>{earned ? b.desc : b.req}</div>
              {earned && earnedData?.earnedAt && (
                <div style={{ fontSize: 11, color: b.color, marginTop: 8, fontWeight: 600 }}>
                  ✓ {new Date(earnedData.earnedAt).toLocaleDateString()}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Best quest scores */}
      {topBestScore.length > 0 && (
        <>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginBottom: 16, color: 'var(--text)' }}>🏆 Best Quest Scores</h2>
          <Card style={{ marginBottom: 32, padding: '16px 20px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {topBestScore.map(([qId, score]) => {
                const quest = QUESTS.find(q => q.id === qId);
                if (!quest) return null;
                return (
                  <div key={qId} style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <span style={{ fontSize: 24 }}>{quest.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 14, color: 'var(--text)' }}>{quest.title}</div>
                      <ProgressBar value={score} max={100} color={quest.color} />
                    </div>
                    <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, color: quest.color, fontSize: 18 }}>{score}%</span>
                  </div>
                );
              })}
            </div>
          </Card>
        </>
      )}

      {/* Leaderboard */}
      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginBottom: 16, color: 'var(--text)' }}>📊 Leaderboard</h2>
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        {/* User's rank highlight */}
        {studentName && (
          <div style={{
            padding: '14px 20px',
            background: 'rgba(74,222,128,0.08)',
            borderBottom: '1px solid rgba(74,222,128,0.15)',
            display: 'flex', alignItems: 'center', gap: 14,
          }}>
            <span style={{ width: 32, textAlign: 'center', fontFamily: 'var(--font-display)', fontWeight: 800, color: '#4ade80', fontSize: 16 }}>#{userRank}</span>
            <span style={{ fontSize: 20 }}>🎓</span>
            <span style={{ flex: 1, fontWeight: 700, color: '#4ade80' }}>{studentName} (You)</span>
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, color: '#4ade80' }}>Lv {level}</span>
            <span style={{ fontWeight: 700, color: '#4ade80', fontFamily: 'var(--font-mono)', fontSize: 14 }}>{xp} XP</span>
          </div>
        )}
        {lb.map((entry, i) => (
          <div key={i} style={{
            padding: '14px 20px',
            borderBottom: i < lb.length - 1 ? '1px solid var(--border2)' : 'none',
            display: 'flex', alignItems: 'center', gap: 14,
            background: entry.rank <= 3 ? `rgba(${entry.rank === 1 ? '251,191,36' : entry.rank === 2 ? '203,213,225' : '234,179,8'},0.04)` : 'transparent',
          }}>
            <span style={{ width: 32, textAlign: 'center', fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 16, color: entry.rank === 1 ? '#fbbf24' : entry.rank === 2 ? '#94a3b8' : entry.rank === 3 ? '#d97706' : 'var(--text3)' }}>
              {entry.rank <= 3 ? ['🥇','🥈','🥉'][entry.rank - 1] : `#${entry.rank}`}
            </span>
            <span style={{ fontSize: 20 }}>{entry.badge}</span>
            <span style={{ flex: 1, fontWeight: 600, color: 'var(--text)', fontSize: 15 }}>{entry.name}</span>
            <span style={{ background: 'var(--surface2)', padding: '3px 10px', borderRadius: 10, fontSize: 12, color: 'var(--text2)', fontWeight: 600 }}>Lv {entry.level}</span>
            <span style={{ fontWeight: 700, color: '#fbbf24', fontFamily: 'var(--font-mono)', fontSize: 14 }}>{entry.xp.toLocaleString()} XP</span>
          </div>
        ))}
      </Card>

      <style>{`@keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }`}</style>
    </div>
  );
}
