import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSessionStore } from '../store/sessionStore';
import { validateSession, startAttempt, submitAnswer, finishAttempt } from '../api';
import { Btn, Card, Input, Spinner, ProgressBar } from '../components/ui';

// ── Timer ──────────────────────────────────────────────────────────────────────
function Timer({ expiresAt, onExpire }) {
  const [remaining, setRemaining] = useState(0);
  useEffect(() => {
    const tick = () => {
      const left = Math.max(0, new Date(expiresAt) - new Date());
      setRemaining(left);
      if (left === 0) onExpire?.();
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [expiresAt]);

  const mins = Math.floor(remaining / 60000);
  const secs = Math.floor((remaining % 60000) / 1000);
  const pct = expiresAt ? Math.max(0, remaining / (new Date(expiresAt) - new Date(expiresAt) + 7200000)) : 1;
  const urgent = mins < 5;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'var(--surface)', border: `1px solid ${urgent ? 'rgba(251,113,133,0.4)' : 'var(--border)'}`, borderRadius: 10, padding: '10px 16px' }}>
      <span style={{ fontSize: 18 }}>⏱</span>
      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 18, color: urgent ? '#fb7185' : '#4ade80', minWidth: 60 }}>
        {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
      </span>
    </div>
  );
}

// ── Question View ─────────────────────────────────────────────────────────────
function QuestionView({ question, currentAnswer, onAnswer, qIdx, total }) {
  const [localText, setLocalText] = useState(currentAnswer?.answer_text || '');
  const [localSelected, setLocalSelected] = useState(currentAnswer?.selected_options || []);

  const isChoice = ['single_choice', 'multiple_choice'].includes(question.type);
  const isMultiple = question.type === 'multiple_choice';

  const toggleOption = (id) => {
    if (!isMultiple) {
      const next = [id];
      setLocalSelected(next);
      onAnswer({ selected_options: next, answer_text: '' });
    } else {
      const next = localSelected.includes(id) ? localSelected.filter(x => x !== id) : [...localSelected, id];
      setLocalSelected(next);
      onAnswer({ selected_options: next, answer_text: '' });
    }
  };

  const handleTextChange = (val) => {
    setLocalText(val);
    onAnswer({ answer_text: val, selected_options: [] });
  };

  useEffect(() => {
    setLocalText(currentAnswer?.answer_text || '');
    setLocalSelected(currentAnswer?.selected_options || []);
  }, [question.id]);

  const diffColor = { easy: '#4ade80', medium: '#fbbf24', hard: '#fb7185' }[question.difficulty] || '#9ab89e';

  return (
    <div style={{ animation: 'fadeUp 0.35s ease' }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 12, color: 'var(--text3)', fontWeight: 600 }}>Q{qIdx + 1}/{total}</span>
        <span style={{ padding: '2px 10px', background: `rgba(${diffColor === '#4ade80' ? '74,222,128' : diffColor === '#fbbf24' ? '251,191,36' : '251,113,133'},0.15)`, color: diffColor, borderRadius: 20, fontSize: 11, fontWeight: 700 }}>
          {question.difficulty}
        </span>
        <span style={{ padding: '2px 10px', background: 'var(--surface3)', color: 'var(--text2)', borderRadius: 20, fontSize: 11, fontWeight: 700 }}>
          {question.type === 'single_choice' ? '◉ Single choice' : question.type === 'multiple_choice' ? '☑ Multiple choice' : question.type === 'code' ? '⌨ Code' : '✎ Text'}
        </span>
        {question.language && (
          <span style={{ padding: '2px 10px', background: 'var(--amber-dim)', color: '#fbbf24', borderRadius: 20, fontSize: 11, fontWeight: 700 }}>{question.language}</span>
        )}
      </div>

      <div style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(16px, 3vw, 20px)', fontWeight: 700, color: 'var(--text)', marginBottom: 24, lineHeight: 1.5 }}>
        {question.text}
      </div>

      {isChoice && question.options?.map(opt => {
        const sel = localSelected.includes(opt.id);
        return (
          <button key={opt.id} onClick={() => toggleOption(opt.id)} style={{
            display: 'block', width: '100%', textAlign: 'left',
            marginBottom: 10, padding: '14px 18px', borderRadius: 10,
            background: sel ? 'var(--green-dim)' : 'var(--surface2)',
            border: `2px solid ${sel ? 'rgba(74,222,128,0.5)' : 'var(--border)'}`,
            color: sel ? '#4ade80' : 'var(--text)',
            fontSize: 15, fontWeight: sel ? 600 : 400,
            cursor: 'pointer', fontFamily: 'var(--font-body)',
            transition: 'all 0.15s',
          }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              width: 22, height: 22, borderRadius: isMultiple ? 4 : '50%',
              background: sel ? '#4ade80' : 'var(--surface3)',
              marginRight: 12, fontSize: 12, color: sel ? '#0a0f0d' : 'var(--text3)',
              flexShrink: 0, fontWeight: 700,
            }}>{sel ? '✓' : ''}</span>
            {opt.text}
          </button>
        );
      })}

      {(question.type === 'text' || question.type === 'code') && (
        <textarea
          value={localText}
          onChange={e => handleTextChange(e.target.value)}
          placeholder={question.type === 'code' ? `Write your ${question.language || 'code'} here...` : 'Type your answer...'}
          style={{
            width: '100%', minHeight: question.type === 'code' ? 180 : 120,
            padding: '14px 16px',
            background: question.type === 'code' ? '#0a0f0d' : 'var(--surface2)',
            border: '1px solid var(--border)', borderRadius: 10,
            color: question.type === 'code' ? '#4ade80' : 'var(--text)',
            fontFamily: question.type === 'code' ? 'var(--font-mono)' : 'var(--font-body)',
            fontSize: 14, lineHeight: 1.6, resize: 'vertical', outline: 'none',
          }}
          onFocus={e => e.target.style.borderColor = 'rgba(74,222,128,0.4)'}
          onBlur={e => e.target.style.borderColor = 'var(--border)'}
        />
      )}
    </div>
  );
}

// ── Main Exam Page ────────────────────────────────────────────────────────────
export default function ExamPage() {
  const nav = useNavigate();
  const { studentName, setStudent, setAttemptId, setCurrentSession } = useSessionStore();

  const [phase, setPhase] = useState('enter'); // enter | preview | exam | submitting | done | error
  const [key, setKey] = useState('');
  const [name, setName] = useState(studentName || '');
  const [session, setSession] = useState(null);
  const [attempt, setAttempt] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [qIdx, setQIdx] = useState(0);
  const [answers, setAnswers] = useState({}); // { question_id: { answer_text, selected_options } }
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleValidate = async () => {
    if (!key.trim()) return;
    setLoading(true); setError('');
    try {
      const sess = await validateSession(key.trim());
      setSession(sess);
      setPhase('preview');
    } catch (e) {
      setError(e.response?.data?.detail || 'Invalid session key. Check with your instructor.');
    } finally { setLoading(false); }
  };

  const handleStart = async () => {
    if (!name.trim()) return;
    setLoading(true); setError('');
    try {
      setStudent(name.trim());
      const data = await startAttempt(key.trim(), name.trim());
      setAttempt(data);
      setAttemptId(data.attempt_id);
      setCurrentSession(session);
      setQuestions(data.questions || []);
      setPhase('exam');
    } catch (e) {
      setError(e.response?.data?.detail || 'Could not start attempt.');
    } finally { setLoading(false); }
  };

  const handleAnswer = (answerData) => {
    setAnswers(prev => ({ ...prev, [questions[qIdx].id]: answerData }));
  };

  const handleNext = async () => {
    // Submit current answer
    const ans = answers[questions[qIdx].id];
    if (ans) {
      try {
        await submitAnswer(attempt.attempt_id, questions[qIdx].id, ans.answer_text || '', ans.selected_options || []);
      } catch (e) { /* continue silently */ }
    }
    if (qIdx < questions.length - 1) setQIdx(i => i + 1);
    else handleFinish();
  };

  const handlePrev = () => { if (qIdx > 0) setQIdx(i => i - 1); };

  const handleFinish = async () => {
    setPhase('submitting');
    setSubmitting(true);
    // Submit remaining answers
    for (const [qid, ans] of Object.entries(answers)) {
      try {
        await submitAnswer(attempt.attempt_id, qid, ans.answer_text || '', ans.selected_options || []);
      } catch {}
    }
    try {
      const res = await finishAttempt(attempt.attempt_id);
      setResult(res);
      setPhase('done');
    } catch (e) {
      setError('Error finalizing exam: ' + (e.response?.data?.detail || e.message));
      setPhase('error');
    } finally { setSubmitting(false); }
  };

  const answeredCount = Object.keys(answers).filter(qid => {
    const a = answers[qid];
    return (a?.answer_text?.trim() || a?.selected_options?.length > 0);
  }).length;

  // ── Phase: Enter ────────────────────────────────────────────────────────────
  if (phase === 'enter') return (
    <div style={{ padding: 'clamp(16px,4vw,40px)', maxWidth: 520, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: 12, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Module 5</div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 800, color: 'var(--text)', marginBottom: 10 }}>🎓 Take Exam</h1>
        <p style={{ color: 'var(--text2)' }}>Enter the session key provided by your instructor</p>
      </div>

      <Card style={{ padding: '28px 32px' }}>
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', fontSize: 12, color: 'var(--text3)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Your Name</label>
          <Input value={name} onChange={setName} placeholder="Enter your name..." icon="👤" />
        </div>
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', fontSize: 12, color: 'var(--text3)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Session Key</label>
          <Input value={key} onChange={setKey} placeholder="e.g. abc123def456..." icon="🔑"
            onKeyDown={e => e.key === 'Enter' && handleValidate()} />
        </div>

        {error && <div style={{ background: 'rgba(251,113,133,0.1)', border: '1px solid rgba(251,113,133,0.3)', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#fb7185', marginBottom: 16 }}>{error}</div>}

        <Btn onClick={handleValidate} disabled={!key.trim() || !name.trim() || loading} size="lg" style={{ width: '100%', justifyContent: 'center' }}>
          {loading ? <><Spinner size={16} color="#0a0f0d" /> Checking...</> : 'Validate Key →'}
        </Btn>
      </Card>

      <div style={{ marginTop: 20, padding: '16px 20px', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>ℹ️ How it works</div>
        <ul style={{ paddingLeft: 16, color: 'var(--text3)', fontSize: 13, lineHeight: 1.8 }}>
          <li>Get a session key from your instructor</li>
          <li>Enter your name and the key above</li>
          <li>Answer all questions before time runs out</li>
          <li>Your results are saved automatically</li>
        </ul>
      </div>
    </div>
  );

  // ── Phase: Preview ──────────────────────────────────────────────────────────
  if (phase === 'preview' && session) return (
    <div style={{ padding: 'clamp(16px,4vw,40px)', maxWidth: 580, margin: '0 auto' }}>
      <div style={{ marginBottom: 28 }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 800, color: 'var(--text)', marginBottom: 8 }}>Session Details</h2>
      </div>

      <Card style={{ padding: '24px 28px', marginBottom: 20 }}>
        <div style={{ fontSize: 13, color: 'var(--text3)', marginBottom: 16 }}>You're about to start:</div>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, color: 'var(--text)', marginBottom: 20 }}>{session.test_title}</h3>

        {session.title && <div style={{ color: 'var(--text2)', fontSize: 14, marginBottom: 16, padding: '8px 14px', background: 'var(--surface2)', borderRadius: 8 }}>📌 {session.title}</div>}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
          {[
            { icon: '🎯', label: 'Type', value: session.is_training ? 'Training' : 'Exam' },
            { icon: '⏱', label: 'Expires', value: session.expires_at ? new Date(session.expires_at).toLocaleTimeString() : '∞' },
            { icon: '🔄', label: 'Max attempts', value: session.max_attempts_per_student ?? '∞' },
            { icon: '✅', label: 'Status', value: session.is_valid ? 'Active' : 'Expired' },
          ].map(({ icon, label, value }) => (
            <div key={label} style={{ background: 'var(--surface2)', borderRadius: 10, padding: '12px 14px' }}>
              <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 4 }}>{icon} {label}</div>
              <div style={{ fontWeight: 700, color: 'var(--text)', fontSize: 14 }}>{String(value)}</div>
            </div>
          ))}
        </div>

        {error && <div style={{ background: 'rgba(251,113,133,0.1)', border: '1px solid rgba(251,113,133,0.3)', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#fb7185', marginBottom: 16 }}>{error}</div>}

        <div style={{ display: 'flex', gap: 12 }}>
          <Btn onClick={handleStart} disabled={!session.is_valid || loading} size="lg" style={{ flex: 1, justifyContent: 'center' }}>
            {loading ? <><Spinner size={16} color="#0a0f0d" /> Starting...</> : `Start as ${name} →`}
          </Btn>
          <Btn variant="ghost" onClick={() => setPhase('enter')}>Back</Btn>
        </div>
      </Card>
    </div>
  );

  // ── Phase: Exam ─────────────────────────────────────────────────────────────
  if (phase === 'exam' && questions.length > 0) {
    const q = questions[qIdx];
    return (
      <div style={{ padding: 'clamp(16px,4vw,32px)', maxWidth: 780, margin: '0 auto' }}>
        {/* Exam header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ fontSize: 13, color: 'var(--text2)', fontWeight: 600 }}>{attempt?.test_title}</div>
            <div style={{ fontSize: 12, color: 'var(--text3)' }}>{name}</div>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ fontSize: 13, color: 'var(--text2)', background: 'var(--surface)', padding: '8px 14px', borderRadius: 8, border: '1px solid var(--border)' }}>
              ✎ {answeredCount}/{questions.length} answered
            </div>
            {session?.expires_at && !session.is_training && (
              <Timer expiresAt={session.expires_at} onExpire={handleFinish} />
            )}
          </div>
        </div>

        {/* Progress */}
        <div style={{ marginBottom: 20 }}>
          <ProgressBar value={qIdx + 1} max={questions.length} color="#a78bfa" />
        </div>

        {/* Question dots */}
        <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
          {questions.map((question, i) => {
            const ans = answers[question.id];
            const hasAns = ans?.answer_text?.trim() || ans?.selected_options?.length > 0;
            return (
              <button key={question.id} onClick={() => setQIdx(i)} style={{
                width: 32, height: 32, borderRadius: 8, border: 'none',
                background: i === qIdx ? '#a78bfa' : hasAns ? 'rgba(74,222,128,0.2)' : 'var(--surface2)',
                color: i === qIdx ? '#fff' : hasAns ? '#4ade80' : 'var(--text3)',
                fontWeight: 700, fontSize: 12, cursor: 'pointer',
                border: `1px solid ${i === qIdx ? '#a78bfa' : hasAns ? 'rgba(74,222,128,0.3)' : 'var(--border)'}`,
              }}>{i + 1}</button>
            );
          })}
        </div>

        {/* Question card */}
        <Card style={{ padding: 'clamp(20px, 4vw, 36px)', marginBottom: 20 }}>
          <QuestionView
            question={q}
            currentAnswer={answers[q.id]}
            onAnswer={handleAnswer}
            qIdx={qIdx}
            total={questions.length}
          />
        </Card>

        {/* Navigation */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
          <Btn variant="ghost" onClick={handlePrev} disabled={qIdx === 0}>← Prev</Btn>
          <div style={{ display: 'flex', gap: 10 }}>
            {qIdx < questions.length - 1
              ? <Btn onClick={handleNext}>Next →</Btn>
              : <Btn variant="amber" onClick={handleFinish} disabled={submitting}>
                  {submitting ? <><Spinner size={16} color="#0a0f0d" /> Submitting...</> : '✓ Submit Exam'}
                </Btn>
            }
          </div>
        </div>

        <style>{`@keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }`}</style>
      </div>
    );
  }

  // ── Phase: Submitting ───────────────────────────────────────────────────────
  if (phase === 'submitting') return (
    <div style={{ minHeight: '60vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
      <Spinner size={48} />
      <p style={{ color: 'var(--text2)', fontSize: 16 }}>Submitting your exam...</p>
    </div>
  );

  // ── Phase: Done ─────────────────────────────────────────────────────────────
  if (phase === 'done' && result) {
    const pct = Math.round(result.score);
    const grade = pct >= 80 ? 'Excellent' : pct >= 60 ? 'Good' : pct >= 40 ? 'Pass' : 'Need Practice';
    const gradeColor = pct >= 80 ? '#4ade80' : pct >= 60 ? '#38bdf8' : pct >= 40 ? '#fbbf24' : '#fb7185';
    return (
      <div style={{ padding: 'clamp(20px,4vw,40px)', maxWidth: 600, margin: '0 auto', textAlign: 'center' }}>
        <div style={{ fontSize: 80, marginBottom: 20 }}>{pct >= 80 ? '🏆' : pct >= 60 ? '⭐' : pct >= 40 ? '💪' : '📚'}</div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 800, color: gradeColor, marginBottom: 8 }}>{grade}!</h1>
        <p style={{ color: 'var(--text2)', fontSize: 16, marginBottom: 32 }}>Exam completed, {result.student_name}</p>

        <Card style={{ padding: '24px 28px', marginBottom: 24, textAlign: 'left' }}>
          <div style={{ fontSize: 64, textAlign: 'center', fontFamily: 'var(--font-display)', fontWeight: 800, color: gradeColor, marginBottom: 8 }}>{pct}%</div>
          <ProgressBar value={pct} max={100} color={gradeColor} />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 20 }}>
            {[
              { label: 'Correct', value: result.correct, icon: '✓', color: '#4ade80' },
              { label: 'Total', value: result.total_questions, icon: '?', color: 'var(--text2)' },
              { label: 'Answered', value: result.answered, icon: '✎', color: '#38bdf8' },
              { label: 'Pending', value: result.pending_grading, icon: '⏳', color: '#fbbf24' },
            ].map(({ label, value, icon, color }) => (
              <div key={label} style={{ background: 'var(--surface2)', borderRadius: 10, padding: '14px', textAlign: 'center' }}>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 24, fontWeight: 800, color }}>{icon} {value}</div>
                <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 4 }}>{label}</div>
              </div>
            ))}
          </div>

          {result.duration_seconds && (
            <div style={{ marginTop: 16, textAlign: 'center', fontSize: 13, color: 'var(--text3)' }}>
              ⏱ Completed in {Math.floor(result.duration_seconds / 60)}m {Math.floor(result.duration_seconds % 60)}s
            </div>
          )}
        </Card>

        {result.pending_grading > 0 && (
          <div style={{ background: 'var(--amber-dim)', border: '1px solid rgba(251,191,36,0.25)', borderRadius: 10, padding: '12px 16px', fontSize: 13, color: '#fbbf24', marginBottom: 16 }}>
            ⏳ {result.pending_grading} answer(s) are pending AI/manual grading. Your final score may change.
          </div>
        )}

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Btn onClick={() => { setPhase('enter'); setKey(''); setQIdx(0); setAnswers({}); }}>Take Another Exam</Btn>
          <Btn variant="ghost" onClick={() => nav('/dashboard')}>Dashboard</Btn>
        </div>
      </div>
    );
  }

  // ── Phase: Error ────────────────────────────────────────────────────────────
  if (phase === 'error') return (
    <div style={{ padding: 40, textAlign: 'center', maxWidth: 500, margin: '0 auto' }}>
      <div style={{ fontSize: 60, marginBottom: 20 }}>❌</div>
      <h2 style={{ color: '#fb7185', marginBottom: 12 }}>Something went wrong</h2>
      <p style={{ color: 'var(--text2)', marginBottom: 24 }}>{error}</p>
      <Btn onClick={() => setPhase('enter')}>Try Again</Btn>
    </div>
  );

  return null;
}
