import React, { useState } from 'react';
import { STORIES } from '../data/content';
import { useProgressStore } from '../store/progressStore';
import { Btn, Card, Input } from '../components/ui';

function MarkdownRenderer({ content }) {
  const lines = content.split('\n');
  const elements = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith('# ')) {
      elements.push(<h1 key={i} style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 800, color: 'var(--text)', marginBottom: 20, paddingBottom: 12, borderBottom: '1px solid var(--border)' }}>{line.slice(2)}</h1>);
    } else if (line.startsWith('## ')) {
      elements.push(<h2 key={i} style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--green)', marginBottom: 12, marginTop: 28 }}>{line.slice(3)}</h2>);
    } else if (line.startsWith('```')) {
      const lang = line.slice(3);
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      elements.push(
        <div key={i} style={{ background: '#0a0f0d', border: '1px solid var(--border)', borderRadius: 10, padding: '16px 20px', margin: '16px 0', overflow: 'auto' }}>
          {lang && <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 8, fontFamily: 'var(--font-mono)', textTransform: 'uppercase' }}>{lang}</div>}
          <pre style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: '#4ade80', lineHeight: 1.7, margin: 0, whiteSpace: 'pre-wrap' }}>{codeLines.join('\n')}</pre>
        </div>
      );
    } else if (line.trim() === '') {
      // skip
    } else {
      // Inline formatting
      const rendered = line
        .replace(/\*\*([^*]+)\*\*/g, '<strong style="color:var(--text);font-weight:700">$1</strong>')
        .replace(/`([^`]+)`/g, '<code style="background:var(--surface3);padding:2px 6px;border-radius:4px;font-size:0.9em;color:#fbbf24;font-family:var(--font-mono)">$1</code>');
      elements.push(<p key={i} style={{ color: 'var(--text2)', lineHeight: 1.9, marginBottom: 12, fontSize: 15 }} dangerouslySetInnerHTML={{ __html: rendered }} />);
    }
    i++;
  }
  return <>{elements}</>;
}

export default function StoriesPage() {
  const { readStories, readStory } = useProgressStore();
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('All');

  const categories = ['All', ...new Set(STORIES.map(s => s.category))];
  const filtered = STORIES.filter(s => {
    const matchSearch = s.title.toLowerCase().includes(search.toLowerCase()) || s.description.toLowerCase().includes(search.toLowerCase());
    const matchCat = filter === 'All' || s.category === filter;
    return matchSearch && matchCat;
  });

  const openStory = (story) => {
    setSelected(story);
    readStory(story.id);
  };

  if (selected) {
    return (
      <div style={{ padding: 'clamp(16px,4vw,40px)', maxWidth: 820, margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 28 }}>
          <button onClick={() => setSelected(null)} style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 14px', color: 'var(--text2)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-body)' }}>← Back</button>
          <div style={{ display: 'flex', align: 'center', gap: 10 }}>
            <span style={{ fontSize: 28 }}>{selected.icon}</span>
            <div>
              <div style={{ fontSize: 11, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{selected.category} · {selected.readTime}</div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 18, fontWeight: 700, color: 'var(--text)' }}>{selected.title}</h2>
            </div>
          </div>
          {readStories.includes(selected.id) && (
            <span style={{ marginLeft: 'auto', fontSize: 12, color: '#4ade80', fontWeight: 700, background: 'rgba(74,222,128,0.1)', padding: '4px 12px', borderRadius: 20, border: '1px solid rgba(74,222,128,0.2)' }}>✓ Read</span>
          )}
        </div>

        <Card style={{ padding: 'clamp(20px, 4vw, 40px)' }}>
          <MarkdownRenderer content={selected.content} />
          <div style={{ marginTop: 32, paddingTop: 20, borderTop: '1px solid var(--border)', display: 'flex', gap: 12 }}>
            <Btn onClick={() => setSelected(null)} variant="ghost">← Back to Stories</Btn>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: 'clamp(16px,4vw,40px)', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 12, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>Module 3</div>
        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(24px,4vw,36px)', fontWeight: 800, color: 'var(--text)', marginBottom: 10 }}>📜 Read Stories</h1>
        <p style={{ color: 'var(--text2)', fontSize: 15 }}>Deepen your knowledge with guides and concepts</p>
      </div>

      {/* Search + filter */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <Input value={search} onChange={setSearch} placeholder="Search stories..." icon="🔍" />
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {categories.map(cat => (
            <button key={cat} onClick={() => setFilter(cat)} style={{
              padding: '10px 16px', borderRadius: 10, fontSize: 13, fontWeight: 600,
              background: filter === cat ? 'var(--green-dim)' : 'var(--surface)',
              border: `1px solid ${filter === cat ? 'rgba(74,222,128,0.3)' : 'var(--border)'}`,
              color: filter === cat ? '#4ade80' : 'var(--text2)', cursor: 'pointer', fontFamily: 'var(--font-body)',
            }}>{cat}</button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gap: 14 }}>
        {filtered.map((story, i) => {
          const isRead = readStories.includes(story.id);
          return (
            <div key={story.id} onClick={() => openStory(story)} style={{
              background: 'var(--surface)', border: `1px solid ${isRead ? 'rgba(74,222,128,0.2)' : 'var(--border)'}`,
              borderRadius: 16, padding: '20px 24px',
              cursor: 'pointer', transition: 'all 0.2s',
              display: 'flex', gap: 20, alignItems: 'center',
              animation: `fadeUp ${0.3 + i * 0.08}s ease both`,
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.borderColor = 'rgba(74,222,128,0.3)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.borderColor = isRead ? 'rgba(74,222,128,0.2)' : 'var(--border)'; }}>
              <div style={{
                width: 52, height: 52, borderRadius: 12, flexShrink: 0,
                background: `rgba(0,0,0,0.3)`, border: `1px solid ${story.color}33`,
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26,
              }}>{story.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 6, flexWrap: 'wrap' }}>
                  <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--text)' }}>{story.title}</h3>
                  <span style={{ fontSize: 11, color: story.color, background: `rgba(0,0,0,0.3)`, padding: '2px 8px', borderRadius: 10, fontWeight: 700 }}>{story.category}</span>
                  {isRead && <span style={{ fontSize: 11, color: '#4ade80', fontWeight: 700 }}>✓ Read</span>}
                </div>
                <p style={{ fontSize: 13, color: 'var(--text3)', marginBottom: 6 }}>{story.description}</p>
                <span style={{ fontSize: 12, color: 'var(--text3)' }}>⏱ {story.readTime}</span>
              </div>
              <div style={{ fontSize: 18, color: 'var(--text3)' }}>→</div>
            </div>
          );
        })}
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: 60, color: 'var(--text3)' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
            <p>No stories found matching your search</p>
          </div>
        )}
      </div>
      <style>{`@keyframes fadeUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }`}</style>
    </div>
  );
}
