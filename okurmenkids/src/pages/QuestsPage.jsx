import React, { useState, useEffect, useRef } from 'react';
import { QUESTS, FLEXBOX_LEVELS, TYPING_SNIPPETS } from '../data/content';
import { useProgressStore } from '../store/progressStore';
import { Btn, Card, DiffBadge } from '../components/ui';

// ── Flexbox Froggy Game ───────────────────────────────────────────────────────
function FlexboxGame({ onComplete }) {
  const [levelIdx, setLevelIdx] = useState(0);
  const [selected, setSelected] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [score, setScore] = useState(0);

  const level = FLEXBOX_LEVELS[levelIdx];

  const check = () => {
    const correct = selected === level.correct;
    setFeedback(correct);
    if (correct) setScore(s => s + 20);
    setTimeout(() => {
      setFeedback(null);
      setSelected('');
      if (levelIdx < FLEXBOX_LEVELS.length - 1) setLevelIdx(i => i + 1);
      else onComplete(score + (correct ? 20 : 0));
    }, 1200);
  };

  // Compute frog positions based on selection
  const flexStyle = { display: 'flex', width: '100%', height: '100%' };
  const prop = level.property === 'align-items' ? 'alignItems' : 'justifyContent';
  if (level.property === 'both') { flexStyle.justifyContent = selected || 'flex-start'; flexStyle.alignItems = selected || 'flex-start'; }
  else flexStyle[prop] = selected || 'flex-start';

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 4 }}>Level {levelIdx + 1} / {FLEXBOX_LEVELS.length}</div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: 'var(--text)' }}>{level.instruction}</h3>
          <p style={{ fontSize: 13, color: 'var(--text3)', marginTop: 4 }}>💡 {level.hint}</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#4ade80' }}>{score}</div>
          <div style={{ fontSize: 11, color: 'var(--text3)' }}>Score</div>
        </div>
      </div>

      {/* Game area */}
      <div style={{
        background: 'linear-gradient(135deg, #0a1f10, #061208)',
        border: '2px solid rgba(74,222,128,0.2)',
        borderRadius: 16,
        height: 160,
        marginBottom: 20,
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Lily pads background */}
        <div style={{ position: 'absolute', inset: 0, opacity: 0.3, background: 'radial-gradient(circle at 50% 80%, rgba(74,222,128,0.2), transparent 50%)' }} />
        <div style={{ ...flexStyle, position: 'absolute', inset: 0, padding: '0 20px' }}>
          {level.frogs.map((f, i) => (
            <div key={i} style={{ fontSize: 36, display: 'flex', alignItems: 'flex-end', paddingBottom: 16, position: 'relative' }}>
              <div style={{ position: 'absolute', bottom: 4, left: '50%', transform: 'translateX(-50%)', width: 44, height: 12, background: 'rgba(74,222,128,0.25)', borderRadius: '50%', border: '1px solid rgba(74,222,128,0.4)' }} />
              {f.emoji}
            </div>
          ))}
        </div>
        {feedback !== null && (
          <div style={{
            position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: feedback ? 'rgba(74,222,128,0.15)' : 'rgba(251,113,133,0.15)',
            fontSize: 48, borderRadius: 14,
          }}>
            {feedback ? '🎉' : '❌'}
          </div>
        )}
      </div>

      {/* Property selector */}
      <div style={{ marginBottom: 14 }}>
        <code style={{ fontSize: 14, color: '#fbbf24', fontFamily: 'var(--font-mono)' }}>
          {level.property === 'both' ? 'justify-content & align-items' : level.property}: <span style={{ color: '#4ade80' }}>{selected || '?'}</span>;
        </code>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 20 }}>
        {level.options.map(opt => (
          <button key={opt} onClick={() => setSelected(opt)} style={{
            padding: '8px 18px', borderRadius: 8,
            background: selected === opt ? 'var(--green-dim)' : 'var(--surface2)',
            border: `1px solid ${selected === opt ? 'rgba(74,222,128,0.4)' : 'var(--border)'}`,
            color: selected === opt ? '#4ade80' : 'var(--text2)',
            fontFamily: 'var(--font-mono)', fontSize: 13, cursor: 'pointer',
            transition: 'all 0.15s',
          }}>{opt}</button>
        ))}
      </div>
      <Btn onClick={check} disabled={!selected}>Apply! 🐸</Btn>
    </div>
  );
}

// ── Typing Game ───────────────────────────────────────────────────────────────
function TypingGame({ onComplete }) {
  const [snippetIdx, setSnippetIdx] = useState(0);
  const [typed, setTyped] = useState('');
  const [startTime, setStartTime] = useState(null);
  const [wpm, setWpm] = useState(0);
  const [done, setDone] = useState(false);
  const [score, setScore] = useState(0);
  const inputRef = useRef();
  const snippet = TYPING_SNIPPETS[snippetIdx];

  const handleType = (e) => {
    const val = e.target.value;
    if (!startTime) setStartTime(Date.now());
    setTyped(val);
    if (val === snippet.code) {
      const elapsed = (Date.now() - startTime) / 60000;
      const words = snippet.code.split(' ').length;
      const currentWpm = Math.round(words / elapsed);
      setWpm(currentWpm);
      const pts = Math.min(100, currentWpm * 2);
      setScore(s => s + pts);
      if (snippetIdx < TYPING_SNIPPETS.length - 1) {
        setTimeout(() => { setSnippetIdx(i => i + 1); setTyped(''); setStartTime(null); }, 800);
      } else {
        setDone(true);
        setTimeout(() => onComplete(score + pts), 1000);
      }
    }
  };

  const chars = snippet.code.split('');
  const typedChars = typed.split('');

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ fontSize: 13, color: 'var(--text3)' }}>Snippet {snippetIdx + 1}/{TYPING_SNIPPETS.length}</div>
        <div style={{ fontFamily: 'var(--font-mono)', color: '#fbbf24' }}>{wpm > 0 ? `${wpm} WPM` : ''}</div>
      </div>

      <div style={{
        background: '#0a0f0d', border: '1px solid var(--border)',
        borderRadius: 12, padding: '20px 24px', marginBottom: 16,
        fontFamily: 'var(--font-mono)', fontSize: 16, lineHeight: 2,
        letterSpacing: '0.02em',
      }}>
        {chars.map((char, i) => {
          let color = '#4a5568';
          if (i < typedChars.length) {
            color = typedChars[i] === char ? '#4ade80' : '#fb7185';
          }
          if (i === typedChars.length) color = '#fff';
          return <span key={i} style={{ color, background: i === typedChars.length ? 'rgba(255,255,255,0.15)' : 'none', borderRadius: 2 }}>{char}</span>;
        })}
      </div>

      <input
        ref={inputRef}
        value={typed}
        onChange={handleType}
        autoFocus
        placeholder="Start typing..."
        style={{
          width: '100%', padding: '12px 16px',
          background: 'var(--surface2)', border: '1px solid var(--border)',
          borderRadius: 10, color: 'var(--text)', fontFamily: 'var(--font-mono)',
          fontSize: 14, outline: 'none',
        }}
        onFocus={e => e.target.style.borderColor = 'rgba(74,222,128,0.4)'}
        onBlur={e => e.target.style.borderColor = 'var(--border)'}
      />
      <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text3)' }}>Score: {score} pts</div>
    </div>
  );
}

// ── Selector Game ─────────────────────────────────────────────────────────────
function SelectorGame({ onComplete }) {
  const challenges = [
    { target: 'all paragraphs', options: ['p', '.text', '#para', 'div p'], correct: 'p', explanation: 'Element selectors target all elements of that type' },
    { target: 'element with class "btn"', options: ['.btn', '#btn', 'btn', '*btn'], correct: '.btn', explanation: 'Class selectors use a dot prefix' },
    { target: 'element with id "header"', options: ['#header', '.header', 'id=header', '[header]'], correct: '#header', explanation: 'ID selectors use a hash prefix' },
    { target: 'all children of .nav', options: ['.nav > *', '.nav *', '.nav +', '.nav ~'], correct: '.nav > *', explanation: '> selects direct children only' },
  ];
  const [idx, setIdx] = useState(0);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(null);
  const ch = challenges[idx];

  const answer = (opt) => {
    if (answered !== null) return;
    const correct = opt === ch.correct;
    setAnswered(opt);
    if (correct) setScore(s => s + 25);
    setTimeout(() => {
      setAnswered(null);
      if (idx < challenges.length - 1) setIdx(i => i + 1);
      else onComplete(score + (correct ? 25 : 0));
    }, 1500);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
        <span style={{ fontSize: 13, color: 'var(--text3)' }}>Challenge {idx + 1}/{challenges.length}</span>
        <span style={{ color: '#38bdf8', fontWeight: 700 }}>{score} pts</span>
      </div>
      <div style={{ background: 'var(--surface2)', borderRadius: 12, padding: '20px', marginBottom: 20 }}>
        <p style={{ fontSize: 14, color: 'var(--text2)', marginBottom: 8 }}>Select the CSS selector that targets:</p>
        <p style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: '#38bdf8' }}>{ch.target}</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
        {ch.options.map(opt => {
          let bg = 'var(--surface2)', border = 'var(--border)', color = 'var(--text)';
          if (answered !== null) {
            if (opt === ch.correct) { bg = 'rgba(74,222,128,0.1)'; border = 'rgba(74,222,128,0.4)'; color = '#4ade80'; }
            else if (opt === answered) { bg = 'rgba(251,113,133,0.1)'; border = 'rgba(251,113,133,0.4)'; color = '#fb7185'; }
          }
          return (
            <button key={opt} onClick={() => answer(opt)} style={{
              padding: '12px 16px', borderRadius: 10, background: bg, border: `1px solid ${border}`,
              color, fontFamily: 'var(--font-mono)', fontSize: 14, cursor: 'pointer', textAlign: 'center',
            }}>{opt}</button>
          );
        })}
      </div>
      {answered && <p style={{ fontSize: 13, color: '#fbbf24' }}>💡 {ch.explanation}</p>}
    </div>
  );
}

// ── Logic Puzzle Game ─────────────────────────────────────────────────────────
function LogicGame({ onComplete }) {
  const puzzles = [
    { question: 'What does [1,2,3].map(x => x * 2) return?', options: ['[2,4,6]', '[1,2,3,1,2,3]', '[3,6,9]', 'Error'], correct: 0 },
    { question: 'What is typeof null?', options: ['"null"', '"object"', '"undefined"', '"boolean"'], correct: 1 },
    { question: 'What does "==" vs "===" differ in?', options: ['No difference', '=== checks type too', '== is faster', '=== allows null'], correct: 1 },
    { question: 'Which method adds to end of array?', options: ['shift()', 'unshift()', 'push()', 'pop()'], correct: 2 },
    { question: 'What is a closure?', options: ['A CSS property', 'A function with its scope', 'An HTML element', 'A loop'], correct: 1 },
    { question: 'What does "async" keyword do?', options: ['Makes code run faster', 'Returns a Promise', 'Stops execution', 'Delays execution'], correct: 1 },
  ];
  const [idx, setIdx] = useState(0);
  const [score, setScore] = useState(0);
  const [answered, setAnswered] = useState(null);
  const p = puzzles[idx];

  const answer = (i) => {
    if (answered !== null) return;
    setAnswered(i);
    const pts = i === p.correct ? 20 : 0;
    setScore(s => s + pts);
    setTimeout(() => {
      setAnswered(null);
      if (idx < puzzles.length - 1) setIdx(j => j + 1);
      else onComplete(score + pts);
    }, 1200);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
        <span style={{ fontSize: 13, color: 'var(--text3)' }}>Puzzle {idx + 1}/{puzzles.length}</span>
        <span style={{ color: '#a78bfa', fontWeight: 700 }}>{score} pts</span>
      </div>
      <div style={{ background: 'var(--surface2)', borderRadius: 12, padding: '20px', marginBottom: 20 }}>
        <p style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)', lineHeight: 1.5 }}>{p.question}</p>
      </div>
      <div style={{ display: 'grid', gap: 8 }}>
        {p.options.map((opt, i) => {
          let bg = 'var(--surface2)', border = 'var(--border)', color = 'var(--text)';
          if (answered !== null) {
            if (i === p.correct) { bg = 'rgba(74,222,128,0.1)'; border = 'rgba(74,222,128,0.4)'; color = '#4ade80'; }
            else if (i === answered) { bg = 'rgba(251,113,133,0.1)'; border = 'rgba(251,113,133,0.4)'; color = '#fb7185'; }
          }
          return (
            <button key={i} onClick={() => answer(i)} style={{
              padding: '11px 16px', borderRadius: 9, background: bg, border: `1px solid ${border}`,
              color, fontSize: 14, cursor: 'pointer', textAlign: 'left', fontFamily: 'var(--font-body)',
            }}>{opt}</button>
          );
        })}
      </div>
    </div>
  );
}

// ── Main Quests Page ──────────────────────────────────────────────────────────
const GAMES = { flexbox: FlexboxGame, typing: TypingGame, selector: SelectorGame, logic: LogicGame };

export default function QuestsPage() {
  const { completedQuests, scores, completeQuest } = useProgressStore();
  const [activeQuest, setActiveQuest] = useState(null);
  const [result, setResult] = useState(null);

  const handleComplete = (score) => {
    const pct = Math.min(100, Math.round(score));
    completeQuest(activeQuest.id, pct);
    setResult(pct);
  };

  if (activeQuest && result !== null) {
    return (
      <div style={{ padding: 'clamp(20px,4vw,40px)', maxWidth: 600, margin: '0 auto', textAlign: 'center', paddingTop: 80 }}>
        <div style={{ fontSize: 80, marginBottom: 20 }}>{result >= 80 ? '🏆' : result >= 50 ? '⭐' : '💪'}</div>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 30, fontWeight: 800, color: result >= 80 ? '#4ade80' : '#fbbf24', marginBottom: 12 }}>
          {result >= 80 ? 'Amazing!' : result >= 50 ? 'Well Done!' : 'Keep Trying!'}
        </h2>
        <p style={{ color: 'var(--text2)', fontSize: 16, marginBottom: 6 }}>{activeQuest.title}</p>
        <div style={{ fontSize: 40, fontWeight: 800, color: activeQuest.color, margin: '20px 0' }}>{result}%</div>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <Btn onClick={() => { setActiveQuest(null); setResult(null); }}>All Quests</Btn>
          <Btn variant="ghost" onClick={() => setResult(null)}>Try Again</Btn>
        </div>
      </div>
    );
  }

  if (activeQuest) {
    const GameComponent = GAMES[activeQuest.type];
    return (
      <div style={{ padding: 'clamp(16px,4vw,40px)', maxWidth: 700, margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 28 }}>
          <button onClick={() => setActiveQuest(null)} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 14px', color: 'var(--text2)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-body)' }}>← Back</button>
          <div>
            <div style={{ fontSize: 11, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{activeQuest.category}</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text)' }}>{activeQuest.icon} {activeQuest.title}</h2>
          </div>
        </div>
        <Card style={{ padding: '24px 28px' }}>
          <GameComponent onComplete={handleComplete} />
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: 'clamp(16px,4vw,40px)', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: 12, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Module 2</div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(24px,4vw,36px)', fontWeight: 800, color: 'var(--text)', marginBottom: 10 }}>⚔️ Play Quests</h1>
        <p style={{ color: 'var(--text2)', fontSize: 15 }}>Interactive games to master coding concepts</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
        {QUESTS.map((q, i) => {
          const done = completedQuests.includes(q.id);
          const best = scores[q.id];
          return (
            <div key={q.id} onClick={() => setActiveQuest(q)} style={{
              background: q.colorDim, border: `1px solid ${q.color}33`,
              borderRadius: 16, padding: '22px', cursor: 'pointer',
              transition: 'all 0.2s', animation: `fadeUp ${0.3 + i * 0.08}s ease both`,
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px)'; e.currentTarget.style.boxShadow = `0 8px 30px ${q.color}22`; }}
            onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>{q.icon}</div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, fontWeight: 700, color: 'var(--text)' }}>{q.title}</h3>
                <DiffBadge difficulty={q.difficulty} />
              </div>
              <p style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 16, lineHeight: 1.5 }}>{q.description}</p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 12, color: q.color, fontWeight: 700 }}>+{q.xp} XP</span>
                {done ? <span style={{ fontSize: 12, color: '#4ade80', fontWeight: 700 }}>✓ Best: {best}%</span>
                  : <span style={{ fontSize: 12, color: 'var(--text3)' }}>{q.levels} levels</span>}
              </div>
            </div>
          );
        })}
      </div>
      <style>{`@keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }`}</style>
    </div>
  );
}
