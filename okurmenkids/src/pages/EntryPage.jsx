import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSessionStore } from '../store/sessionStore';
import { Btn, Input } from '../components/ui';

export default function EntryPage() {
  const nav = useNavigate();
  const { studentName, setStudent } = useSessionStore();
  const [name, setName] = useState(studentName || '');
  const [step, setStep] = useState('name'); // 'name' | 'ready'

  useEffect(() => {
    if (studentName) nav('/dashboard');
  }, []);

  const handleStart = () => {
    if (!name.trim()) return;
    setStudent(name.trim());
    nav('/dashboard');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20, position: 'relative', overflow: 'hidden' }}>
      {/* Animated background elements */}
      <div style={{ position: 'fixed', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        {[...Array(12)].map((_, i) => (
          <div key={i} style={{
            position: 'absolute',
            left: `${8 + i * 8}%`,
            top: `${15 + (i % 4) * 20}%`,
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: `rgba(74,222,128,${0.04 + (i % 3) * 0.02})`,
            animation: `float ${3 + i * 0.5}s ease-in-out infinite`,
            animationDelay: `${i * 0.3}s`,
            userSelect: 'none',
          }}>
            {['const', 'let', '=>', '{}', '[]', 'fn()', 'div', 'css', '.js', '<>', '//...', 'return'][i]}
          </div>
        ))}
      </div>

      <div style={{ width: '100%', maxWidth: 480, animation: 'fadeUp 0.6s ease forwards' }}>
        {/* Hero icon */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            width: 100, height: 100,
            background: 'linear-gradient(135deg, rgba(74,222,128,0.2), rgba(74,222,128,0.05))',
            border: '1px solid rgba(74,222,128,0.3)',
            borderRadius: 28,
            fontSize: 52,
            marginBottom: 20,
            boxShadow: '0 0 60px rgba(74,222,128,0.2)',
            animation: 'float 3s ease-in-out infinite',
          }}>🦉</div>

          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(32px, 6vw, 52px)',
            fontWeight: 800,
            background: 'linear-gradient(135deg, #4ade80, #22c55e)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: 8,
            lineHeight: 1.1,
          }}>OkurmenKids</h1>

          <p style={{ color: 'var(--text2)', fontSize: 16, lineHeight: 1.5 }}>
            Learn to code through lessons, games, and challenges
          </p>
        </div>

        {/* Features pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', marginBottom: 40 }}>
          {[['📖', 'Lessons'], ['⚔️', 'Quests'], ['📜', 'Stories'], ['🏅', 'Badges'], ['🎓', 'Exams']].map(([icon, label]) => (
            <div key={label} style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 14px',
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 20,
              fontSize: 13,
              color: 'var(--text2)',
            }}>
              <span>{icon}</span>{label}
            </div>
          ))}
        </div>

        {/* Entry card */}
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: 20,
          padding: 32,
          boxShadow: '0 0 60px rgba(74,222,128,0.08)',
        }}>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, marginBottom: 8, color: 'var(--text)' }}>
            What should we call you?
          </h2>
          <p style={{ color: 'var(--text3)', fontSize: 13, marginBottom: 24 }}>
            No account needed. Your progress saves locally.
          </p>

          <div style={{ marginBottom: 20 }}>
            <Input
              value={name}
              onChange={setName}
              placeholder="Enter your name..."
              icon="✏️"
              style={{ fontSize: 16 }}
            />
          </div>

          <Btn
            onClick={handleStart}
            disabled={!name.trim()}
            size="lg"
            style={{ width: '100%', justifyContent: 'center' }}
          >
            Start Learning →
          </Btn>

          <div style={{ marginTop: 16, fontSize: 12, color: 'var(--text3)', textAlign: 'center' }}>
            🔒 No signup required · Progress saved in browser
          </div>
        </div>
      </div>

      <style>{`@keyframes fadeUp { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:translateY(0); } }
@keyframes float { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-8px); } }`}</style>
    </div>
  );
}
