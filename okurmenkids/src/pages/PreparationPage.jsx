import React, { useState } from 'react';
import { LESSONS } from '../data/content';
import { useProgressStore } from '../store/progressStore';
import { Btn, Card, Badge, DiffBadge, ProgressBar } from '../components/ui';

function CodeBlock({ code }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div style={{ position: 'relative', marginTop: 16, marginBottom: 16 }}>
      <div style={{
        background: '#0a0f0d',
        border: '1px solid var(--border)',
        borderRadius: 10,
        padding: '16px 20px',
        overflow: 'auto',
        maxHeight: 300,
      }}>
        <pre style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: '#4ade80', lineHeight: 1.7, margin: 0, whiteSpace: 'pre-wrap' }}>{code}</pre>
      </div>
      <button onClick={copy} style={{
        position: 'absolute', top: 10, right: 10,
        background: 'var(--surface2)', border: '1px solid var(--border)',
        borderRadius: 6, padding: '4px 10px', fontSize: 11,
        color: 'var(--text2)', cursor: 'pointer',
      }}>{copied ? '✓ Copied' : 'Copy'}</button>
    </div>
  );
}

function ContentRenderer({ text }) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/);
  return (
    <span>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**'))
          return <strong key={i} style={{ color: 'var(--green)', fontWeight: 700 }}>{part.slice(2, -2)}</strong>;
        if (part.startsWith('`') && part.endsWith('`'))
          return <code key={i} style={{ background: 'var(--surface3)', padding: '1px 6px', borderRadius: 4, fontSize: '0.9em', color: '#fbbf24', fontFamily: 'var(--font-mono)' }}>{part.slice(1, -1)}</code>;
        return <span key={i}>{part}</span>;
      })}
    </span>
  );
}

function ChapterView({ lesson, chapter, onComplete, onNext, isCompleted }) {
  const [selected, setSelected] = useState(null);
  const [answered, setAnswered] = useState(false);
  const quiz = chapter.quiz;

  const handleAnswer = (idx) => {
    if (answered) return;
    setSelected(idx);
    setAnswered(true);
    if (idx === quiz.correct && !isCompleted) onComplete();
  };

  return (
    <div style={{ animation: 'fadeUp 0.4s ease' }}>
      <div style={{ marginBottom: 24 }}>
        {chapter.content.split('\n\n').map((para, i) => {
          if (para.startsWith('- '))
            return <ul key={i} style={{ paddingLeft: 20, marginBottom: 12, color: 'var(--text2)', lineHeight: 1.8 }}>
              {para.split('\n').map((line, j) => <li key={j} style={{ marginBottom: 4 }}><ContentRenderer text={line.slice(2)} /></li>)}
            </ul>;
          return <p key={i} style={{ color: 'var(--text2)', lineHeight: 1.8, marginBottom: 12, fontSize: 15 }}>
            <ContentRenderer text={para} />
          </p>;
        })}
      </div>

      {chapter.code && <CodeBlock code={chapter.code} />}

      {/* Mini quiz */}
      <div style={{ marginTop: 28 }}>
        <div style={{
          background: 'var(--surface2)', border: '1px solid var(--border)',
          borderRadius: 14, padding: '20px 24px',
        }}>
          <div style={{ fontSize: 12, color: 'var(--text3)', fontWeight: 700, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.08em' }}>✦ Quick Check</div>
          <p style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)', marginBottom: 16 }}>{quiz.question}</p>
          <div style={{ display: 'grid', gap: 8 }}>
            {quiz.options.map((opt, i) => {
              let bg = 'var(--surface)';
              let border = 'var(--border)';
              let color = 'var(--text)';
              if (answered) {
                if (i === quiz.correct) { bg = 'rgba(74,222,128,0.1)'; border = 'rgba(74,222,128,0.4)'; color = '#4ade80'; }
                else if (i === selected && i !== quiz.correct) { bg = 'rgba(251,113,133,0.1)'; border = 'rgba(251,113,133,0.4)'; color = '#fb7185'; }
              } else if (selected === i) { bg = 'var(--surface2)'; border = 'rgba(74,222,128,0.3)'; }
              return (
                <button key={i} onClick={() => handleAnswer(i)} style={{
                  textAlign: 'left', padding: '10px 16px',
                  background: bg, border: `1px solid ${border}`,
                  borderRadius: 8, color, fontSize: 14, fontWeight: 500,
                  cursor: answered ? 'default' : 'pointer',
                  transition: 'all 0.15s',
                  fontFamily: 'var(--font-body)',
                }}>
                  {answered && i === quiz.correct ? '✓ ' : answered && i === selected ? '✗ ' : ''}{opt}
                </button>
              );
            })}
          </div>
          {answered && (
            <div style={{ marginTop: 14, padding: '10px 14px', background: selected === quiz.correct ? 'rgba(74,222,128,0.1)' : 'rgba(251,113,133,0.1)', borderRadius: 8, fontSize: 13, color: selected === quiz.correct ? '#4ade80' : '#fb7185' }}>
              {selected === quiz.correct ? '🎉 Correct! Well done.' : `💡 The correct answer was: "${quiz.options[quiz.correct]}"`}
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: 20, display: 'flex', gap: 12 }}>
        <Btn onClick={onNext} disabled={!answered}>
          {onNext ? 'Next Chapter →' : 'Complete Lesson ✓'}
        </Btn>
      </div>
    </div>
  );
}

export default function PreparationPage() {
  const { completedLessons, completeLesson } = useProgressStore();
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [chapterIdx, setChapterIdx] = useState(0);
  const [lessonDone, setLessonDone] = useState(false);

  const openLesson = (lesson) => {
    setSelectedLesson(lesson);
    setChapterIdx(0);
    setLessonDone(false);
  };

  const nextChapter = () => {
    if (chapterIdx < selectedLesson.chapters.length - 1) {
      setChapterIdx(c => c + 1);
    } else {
      if (!completedLessons.includes(selectedLesson.id)) completeLesson(selectedLesson.id);
      setLessonDone(true);
    }
  };

  if (selectedLesson && lessonDone) {
    return (
      <div style={{ padding: 'clamp(20px,4vw,40px)', maxWidth: 700, margin: '0 auto', textAlign: 'center', paddingTop: 80 }}>
        <div style={{ fontSize: 80, marginBottom: 20, animation: 'float 2s ease-in-out infinite' }}>🎉</div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 32, fontWeight: 800, color: 'var(--green)', marginBottom: 12 }}>Lesson Complete!</h1>
        <p style={{ color: 'var(--text2)', fontSize: 16, marginBottom: 8 }}>{selectedLesson.title}</p>
        <p style={{ color: 'var(--text3)', fontSize: 14, marginBottom: 32 }}>+{selectedLesson.xp} XP earned</p>
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <Btn onClick={() => { setSelectedLesson(null); setLessonDone(false); }}>Back to Lessons</Btn>
        </div>
      </div>
    );
  }

  if (selectedLesson) {
    const chapter = selectedLesson.chapters[chapterIdx];
    const isCompleted = completedLessons.includes(selectedLesson.id);
    return (
      <div style={{ padding: 'clamp(16px,4vw,40px)', maxWidth: 800, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 28 }}>
          <button onClick={() => setSelectedLesson(null)} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 14px', color: 'var(--text2)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-body)' }}>← Back</button>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{selectedLesson.category}</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 700, color: 'var(--text)' }}>{selectedLesson.title}</h2>
          </div>
        </div>

        {/* Progress */}
        <div style={{ marginBottom: 24 }}>
          <ProgressBar value={chapterIdx + 1} max={selectedLesson.chapters.length} color={selectedLesson.color} label={`Chapter ${chapterIdx + 1} of ${selectedLesson.chapters.length}`} />
        </div>

        <Card style={{ padding: '24px 28px' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, marginBottom: 20, color: 'var(--text)', borderBottom: '1px solid var(--border)', paddingBottom: 14 }}>
            {chapter.title}
          </h3>
          <ChapterView
            lesson={selectedLesson}
            chapter={chapter}
            isCompleted={isCompleted}
            onComplete={() => completeLesson(selectedLesson.id)}
            onNext={chapterIdx < selectedLesson.chapters.length - 1 ? nextChapter : null}
          />
          {chapterIdx === selectedLesson.chapters.length - 1 && (
            <div style={{ marginTop: 12 }}>
              <Btn onClick={nextChapter}>Finish Lesson ✓</Btn>
            </div>
          )}
        </Card>

        <style>{`@keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} } @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}`}</style>
      </div>
    );
  }

  return (
    <div style={{ padding: 'clamp(16px,4vw,40px)', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <div style={{ fontSize: 12, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Module 1</div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(24px,4vw,36px)', fontWeight: 800, color: 'var(--text)', marginBottom: 10 }}>📖 Preparation</h1>
        <p style={{ color: 'var(--text2)', fontSize: 15 }}>{completedLessons.length} of {LESSONS.length} lessons completed</p>
      </div>

      <div style={{ display: 'grid', gap: 16 }}>
        {LESSONS.map((lesson, i) => {
          const done = completedLessons.includes(lesson.id);
          return (
            <div
              key={lesson.id}
              onClick={() => openLesson(lesson)}
              style={{
                background: 'var(--surface)',
                border: `1px solid ${done ? 'rgba(74,222,128,0.25)' : 'var(--border)'}`,
                borderRadius: 16,
                padding: '20px 24px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                display: 'flex', alignItems: 'center', gap: 20,
                animation: `fadeUp ${0.3 + i * 0.1}s ease both`,
              }}
              onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'rgba(74,222,128,0.3)'; }}
              onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.borderColor = done ? 'rgba(74,222,128,0.25)' : 'var(--border)'; }}
            >
              <div style={{
                width: 56, height: 56, borderRadius: 14, flexShrink: 0,
                background: lesson.colorDim, display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 28, border: `1px solid ${lesson.color}33`,
              }}>{lesson.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
                  <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 17, fontWeight: 700, color: 'var(--text)' }}>{lesson.title}</h3>
                  <DiffBadge difficulty={lesson.difficulty} />
                  {done && <span style={{ fontSize: 12, color: '#4ade80', fontWeight: 700 }}>✓ Done</span>}
                </div>
                <p style={{ fontSize: 13, color: 'var(--text3)', marginBottom: 8 }}>{lesson.description}</p>
                <div style={{ display: 'flex', gap: 12, fontSize: 12, color: 'var(--text3)' }}>
                  <span>⏱ {lesson.duration}</span>
                  <span>⭐ +{lesson.xp} XP</span>
                  <span>📄 {lesson.chapters.length} chapters</span>
                </div>
              </div>
              <div style={{ fontSize: 20, color: 'var(--text3)' }}>→</div>
            </div>
          );
        })}
      </div>
      <style>{`@keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }`}</style>
    </div>
  );
}
