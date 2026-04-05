/**
 * OkurmenKids Frontend — app.js
 * Production-ready quiz platform
 * Vanilla JS · async/await · zero dependencies
 */

'use strict';

/* ═══════════════════════════════════════════════════════════════════════════
   CONFIG
   ═══════════════════════════════════════════════════════════════════════════ */
const BASE_URL = 'http://127.0.0.1:8000';

const ENDPOINTS = {
  validate:     `${BASE_URL}/api/v1/sessions/validate`,
  startAttempt: `${BASE_URL}/api/v1/attempt/start`,
  submitAnswer: `${BASE_URL}/api/v1/attempt/answer`,
  finish:       `${BASE_URL}/api/v1/attempt/finish`,
  result:       (id) => `${BASE_URL}/api/v1/attempt/${id}/result`,
};

/* ═══════════════════════════════════════════════════════════════════════════
   STATE
   ═══════════════════════════════════════════════════════════════════════════ */
const state = {
  session:       null,  // validated session object
  attempt:       null,  // started attempt object
  questions:     [],    // array of question objects
  currentIdx:    0,     // current question index (0-based)
  answers:       {},    // { [questionId]: AnswerState }
  elapsed:       0,     // seconds elapsed
  timerHandle:   null,  // setInterval reference
  submitting:    {},    // { [questionId]: true } debounce guard
};

/**
 * AnswerState shape:
 * {
 *   submitted:       boolean,
 *   is_correct:      boolean | null,
 *   grading_status:  string,
 *   selectedOptions: string[],   // for choice questions
 *   answerText:      string,     // for text/code questions
 * }
 */

/* ═══════════════════════════════════════════════════════════════════════════
   UTILITIES
   ═══════════════════════════════════════════════════════════════════════════ */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function truncate(str, n) {
  return str && str.length > n ? str.slice(0, n) + '…' : (str || '');
}

/* ── Screen switching ──────────────────────────────────────────────────────── */
function showScreen(id) {
  $$('.screen').forEach(s => { s.classList.remove('active'); });
  const el = $(`#${id}`);
  if (el) el.classList.add('active');
}

/* ── Loading overlay ───────────────────────────────────────────────────────── */
function showLoading(msg = 'Загрузка...') {
  const overlay = $('#loading-overlay');
  const text    = $('#loading-msg');
  if (overlay) overlay.classList.remove('hidden');
  if (text) text.textContent = msg;
}

function hideLoading() {
  const overlay = $('#loading-overlay');
  if (overlay) overlay.classList.add('hidden');
}

/* ── Toast notifications ───────────────────────────────────────────────────── */
const TOAST_ICONS = {
  success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>`,
  error:   `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  info:    `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>`,
  warning: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
};

function toast(message, type = 'info', duration = 3500) {
  const container = $('#toast-container');
  if (!container) return;

  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `${TOAST_ICONS[type] || TOAST_ICONS.info}<span>${esc(message)}</span>`;
  container.appendChild(el);

  setTimeout(() => {
    el.classList.add('out');
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }, duration);
}

/* ── HTTP helper ───────────────────────────────────────────────────────────── */
async function apiFetch(url, options = {}) {
  const config = {
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    ...options,
  };
  if (options.headers) config.headers = { ...config.headers, ...options.headers };

  const res  = await fetch(url, config);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data.detail || data.message || `Ошибка ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

/* ── SVG helpers ───────────────────────────────────────────────────────────── */
const SVG = {
  check: () => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>`,
  x:     () => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
  clock: () => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>`,
  arrowR: () => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>`,
  flag:   () => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>`,
};

/* ═══════════════════════════════════════════════════════════════════════════
   TIMER
   ═══════════════════════════════════════════════════════════════════════════ */
function startTimer() {
  state.elapsed = 0;
  clearInterval(state.timerHandle);
  state.timerHandle = setInterval(() => {
    state.elapsed++;
    renderTimer();
  }, 1000);
}

function stopTimer() {
  clearInterval(state.timerHandle);
  state.timerHandle = null;
}

function renderTimer() {
  const el = $('#timer-val');
  if (!el) return;
  const m = Math.floor(state.elapsed / 60).toString().padStart(2, '0');
  const s = (state.elapsed % 60).toString().padStart(2, '0');
  el.textContent = `${m}:${s}`;

  // Warn when exam session is about to expire
  const timerEl = $('#timer-el');
  if (timerEl && state.session?.session_type === 'exam' && state.session?.expires_at) {
    const remaining = (new Date(state.session.expires_at) - Date.now()) / 1000;
    timerEl.classList.toggle('urgent', remaining < 300);
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCREEN 1 — SESSION ENTRY
   ═══════════════════════════════════════════════════════════════════════════ */
function initEntryScreen() {
  const input  = $('#session-key-input');
  const btn    = $('#validate-btn');

  input.addEventListener('keydown', e => { if (e.key === 'Enter') btn.click(); });
  input.addEventListener('paste', () => {
    setTimeout(() => { if (input.value.trim().length >= 8) btn.click(); }, 120);
  });

  btn.addEventListener('click', async () => {
    const key = input.value.trim();
    if (!key) { toast('Введите ключ сессии', 'warning'); input.focus(); return; }

    const label = btn.querySelector('.btn-label');
    btn.disabled = true;
    label.textContent = 'Проверяем...';
    showLoading('Проверяем ключ сессии...');

    try {
      const session    = await apiFetch(ENDPOINTS.validate, { method: 'POST', body: JSON.stringify({ key }) });
      state.session    = session;
      renderSessionInfo(session);
      showScreen('screen-name');
      $('#student-name-input')?.focus();
      toast('Сессия найдена!', 'success');
    } catch (err) {
      toast(err.message || 'Неверный ключ сессии', 'error');
    } finally {
      hideLoading();
      btn.disabled     = false;
      label.textContent = 'Проверить ключ';
    }
  });
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCREEN 2 — NAME + SESSION INFO
   ═══════════════════════════════════════════════════════════════════════════ */
function renderSessionInfo(session) {
  const panel = $('#session-info-display');
  if (!panel) return;

  const typeLabel = session.session_type === 'exam' ? 'Экзамен' : 'Тренажёр';
  const typeCls   = session.session_type === 'exam' ? 'badge-exam' : 'badge-training';
  const validBadge = session.is_valid
    ? `<span class="badge badge-valid">Активна</span>`
    : `<span class="badge badge-invalid">Истекла</span>`;

  let expiresRow = '';
  if (session.session_type === 'exam' && session.expires_at) {
    const d = new Date(session.expires_at);
    expiresRow = `
      <div class="si-row">
        <span class="si-key">Истекает</span>
        <span class="si-val">${d.toLocaleString('ru', { hour:'2-digit', minute:'2-digit', day:'numeric', month:'short' })}</span>
      </div>`;
  }

  panel.innerHTML = `
    <div class="si-row">
      <span class="si-key">Тест</span>
      <span class="si-val">${esc(session.test_title || '—')}</span>
    </div>
    <div class="si-row">
      <span class="si-key">Тип</span>
      <span class="si-val"><span class="badge ${typeCls}">${typeLabel}</span></span>
    </div>
    <div class="si-row">
      <span class="si-key">Статус</span>
      <span class="si-val">${validBadge}</span>
    </div>
    ${expiresRow}
    ${session.title ? `<div class="si-row"><span class="si-key">Название</span><span class="si-val">${esc(session.title)}</span></div>` : ''}
  `;
}

function initNameScreen() {
  $('#back-to-entry')?.addEventListener('click', () => {
    state.session = null;
    showScreen('screen-entry');
    $('#session-key-input')?.focus();
  });

  const nameInput = $('#student-name-input');
  const startBtn  = $('#start-attempt-btn');

  nameInput?.addEventListener('keydown', e => { if (e.key === 'Enter') startBtn.click(); });

  startBtn?.addEventListener('click', async () => {
    const name = nameInput.value.trim();
    if (!name)        { toast('Введите ваше имя', 'warning'); nameInput.focus(); return; }
    if (name.length < 2) { toast('Имя слишком короткое', 'warning'); return; }

    const label = startBtn.querySelector('.btn-label');
    startBtn.disabled = true;
    label.textContent = 'Запускаем...';
    showLoading('Начинаем тест...');

    try {
      const attempt     = await apiFetch(ENDPOINTS.startAttempt, {
        method: 'POST',
        body: JSON.stringify({ key: state.session.key, student_name: name }),
      });
      state.attempt     = attempt;
      state.questions   = attempt.questions || [];
      state.answers     = {};
      state.currentIdx  = 0;

      if (!state.questions.length) {
        toast('В этом тесте нет вопросов', 'warning');
        return;
      }

      buildTestScreen();
      showScreen('screen-test');
      startTimer();
      toast('Тест начат! Удачи 🎯', 'success');
    } catch (err) {
      toast(err.message || 'Не удалось начать тест', 'error');
    } finally {
      hideLoading();
      startBtn.disabled = false;
      label.textContent = 'Начать тест';
    }
  });
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCREEN 3 — TEST
   ═══════════════════════════════════════════════════════════════════════════ */
function buildTestScreen() {
  $('#hdr-test-title').textContent  = state.attempt.test_title   || '—';
  $('#hdr-student-name').textContent = state.attempt.student_name || '—';
  renderNavDots();
  renderQuestion();
  updateProgress();
}

/* ── Navigation dots ───────────────────────────────────────────────────────── */
function renderNavDots() {
  const nav = $('#q-nav');
  if (!nav) return;

  nav.innerHTML = state.questions.map((q, i) => {
    const ans      = state.answers[q.id];
    const done     = ans?.submitted;
    const isCurr   = i === state.currentIdx;
    return `<button class="q-dot${done ? ' done' : ''}${isCurr ? ' curr' : ''}" data-i="${i}" aria-label="Вопрос ${i+1}">${i+1}</button>`;
  }).join('');

  nav.querySelectorAll('.q-dot').forEach(btn => {
    btn.addEventListener('click', () => {
      autoSaveText();
      state.currentIdx = parseInt(btn.dataset.i, 10);
      renderNavDots();
      renderQuestion();
      updateProgress();
    });
  });
}

/* ── Progress bar ──────────────────────────────────────────────────────────── */
function updateProgress() {
  const total    = state.questions.length;
  const answered = Object.values(state.answers).filter(a => a.submitted).length;
  const pct      = total ? (answered / total) * 100 : 0;

  const bar   = $('#prog-bar');
  const label = $('#prog-label');
  if (bar)   bar.style.width    = `${pct}%`;
  if (label) label.textContent  = `${answered} / ${total}`;
}

/* ════════════════════════════════════════════════════════════════════════════
   CRITICAL RENDER FUNCTION — guarantees every question type is displayed
   ════════════════════════════════════════════════════════════════════════════ */
function renderQuestion() {
  const card = $('#q-card');
  if (!card) return;

  const q = state.questions[state.currentIdx];
  console.log(q)
  /* ── FALLBACK: missing question data ───────────────────────────────────── */
  if (!q) {
    card.innerHTML = `<div class="fallback-state"><p>Вопрос не найден</p></div>`;
    return;
  }

  const ans = state.answers[q.id] || {};

  /* ── Meta labels ───────────────────────────────────────────────────────── */
  const TYPE_LABELS  = { single_choice:'Один ответ', multiple_choice:'Несколько', text:'Текст', code:'Код' };
  const TYPE_CSS     = { single_choice:'qt-single', multiple_choice:'qt-multiple', text:'qt-text', code:'qt-code' };
  const DIFF_LABELS  = { easy:'Лёгкий', medium:'Средний', hard:'Сложный' };
  const DIFF_CSS     = { easy:'diff-easy', medium:'diff-medium', hard:'diff-hard' };

  const typeCss  = TYPE_CSS[q.question_type]  || 'qt-text';
  const typeLabel= TYPE_LABELS[q.question_type] || q.question_type || '?';
  const diffCss  = DIFF_CSS[q.difficulty]     || '';
  const diffLabel= DIFF_LABELS[q.difficulty]  || q.difficulty || '';

  /* ── Answer result pill (already answered) ─────────────────────────────── */
  function resultPillHTML() {
    if (!ans.submitted) return '';
    if (ans.is_correct === true)  return `<div class="result-pill pill-correct">${SVG.check()} Верно</div>`;
    if (ans.is_correct === false) return `<div class="result-pill pill-wrong">${SVG.x()} Неверно</div>`;
    return `<div class="result-pill pill-pending">${SVG.clock()} Ожидает проверки</div>`;
  }
  /* ── Build answer body based on question_type ──────────────────────────── */
  let answerBody = '';

  /* ────────────────────────────────────────────────────────────────────────
     TYPE: single_choice — radio buttons
     GUARANTEE: renders ALL options or fallback message
  ─────────────────────────────────────────────────────────────────────────── */
  if (q.type === 'single_choice') {
    const options = Array.isArray(q.options) && q.options.length ? q.options : null;
    const selected = new Set(ans.selectedOptions || []);

    if (!options) {
      answerBody = `<div class="fallback-state"><p>Варианты ответов не загружены</p></div>`;
    } else {
      const optsHTML = options.map((opt, i) => {
        const isSelected = selected.has(String(opt.id));
        const alpha      = 'ABCDEFGHIJKLMNOP'[i] || String(i + 1);
        return `
          <div class="option${isSelected ? ' radio-selected' : ''}" role="radio"
               aria-checked="${isSelected}" tabindex="0" data-opt-id="${esc(String(opt.id))}">
            <span class="opt-alpha">${alpha}</span>
            <span class="opt-text">${esc(opt.text || '—')}</span>
            <span class="opt-ctrl" aria-hidden="true">
              <span class="opt-ctrl-dot"></span>
            </span>
          </div>`;
      }).join('');

      answerBody = `
        <div class="answer-hint hint-single">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>
          Выберите один правильный ответ
        </div>
        <div class="options-list" role="radiogroup">${optsHTML}</div>
        ${resultPillHTML()}`;
    }
  }

  /* ────────────────────────────────────────────────────────────────────────
     TYPE: multiple_choice — checkboxes
     GUARANTEE: renders ALL options or fallback message
  ─────────────────────────────────────────────────────────────────────────── */
  else if (q.type === 'multiple_choice') {
    const options = Array.isArray(q.options) && q.options.length ? q.options : null;
    const selected = new Set(ans.selectedOptions || []);

    if (!options) {
      answerBody = `<div class="fallback-state"><p>Варианты ответов не загружены</p></div>`;
    } else {
      const optsHTML = options.map((opt, i) => {
        const isSelected = selected.has(String(opt.id));
        const alpha      = 'ABCDEFGHIJKLMNOP'[i] || String(i + 1);
        return `
          <div class="option${isSelected ? ' check-selected' : ''}" role="checkbox"
               aria-checked="${isSelected}" tabindex="0" data-opt-id="${esc(String(opt.id))}">
            <span class="opt-alpha">${alpha}</span>
            <span class="opt-text">${esc(opt.text || '—')}</span>
            <span class="opt-ctrl checkbox" aria-hidden="true">
              <svg class="opt-ctrl-check" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M2 6l3 3 5-5"/></svg>
            </span>
          </div>`;
      }).join('');

      answerBody = `
        <div class="answer-hint hint-multiple">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 12l2 2 4-4"/></svg>
          Выберите все подходящие варианты
        </div>
        <div class="options-list" role="group">${optsHTML}</div>
        ${resultPillHTML()}`;
    }
  }

  /* ────────────────────────────────────────────────────────────────────────
     TYPE: text — free-form textarea
     GUARANTEE: always shows textarea with current value
  ─────────────────────────────────────────────────────────────────────────── */
  else if (q.type === 'text') {
    answerBody = `
      <div class="answer-hint hint-text">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        Развёрнутый ответ в свободной форме
      </div>
      <textarea
        class="answer-textarea"
        id="answer-textarea"
        rows="8"
        placeholder="Введите ваш ответ здесь..."
      >${esc(ans.answerText || '')}</textarea>
      <div class="textarea-footer">
        <span class="char-count" id="char-count">0 символов</span>
        <span class="save-hint">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
          Сохраняется при переходе
        </span>
      </div>
      ${resultPillHTML()}`;
  }

  /* ────────────────────────────────────────────────────────────────────────
     TYPE: code — monospace textarea with editor chrome
     GUARANTEE: always shows code area with current value
  ─────────────────────────────────────────────────────────────────────────── */
  else if (q.type === 'code') {
    const lang = q.language || 'code';
    answerBody = `
      <div class="answer-hint hint-code">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
        Напишите решение на ${esc(lang)}
      </div>
      <div class="code-wrap">
        <div class="code-bar">
          <div class="code-dots">
            <span class="cdot r"></span>
            <span class="cdot y"></span>
            <span class="cdot g"></span>
          </div>
          <div class="code-lang">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:11px;height:11px"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
            ${esc(lang)}
          </div>
          <button class="code-copy" id="code-copy-btn" type="button">Копировать</button>
        </div>
        <textarea
          class="code-textarea"
          id="answer-textarea"
          rows="12"
          placeholder="// Введите ваш код здесь..."
          spellcheck="false"
          autocorrect="off"
          autocapitalize="off"
        >${esc(ans.answerText || '')}</textarea>
      </div>
      <div class="textarea-footer">
        <span class="char-count" id="char-count">0 строк</span>
        <span class="save-hint">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          Сохраняется при переходе
        </span>
      </div>
      ${resultPillHTML()}`;
  }

  /* ────────────────────────────────────────────────────────────────────────
     UNKNOWN TYPE — always fallback, never blank
  ─────────────────────────────────────────────────────────────────────────── */
  else {
    answerBody = `
      <div class="answer-hint hint-text">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
        Введите ваш ответ (тип: ${esc(q.type || 'unknown')})
      </div>
      <textarea class="answer-textarea" id="answer-textarea" rows="6"
        placeholder="Ваш ответ...">${esc(ans.answerText || '')}</textarea>
      ${resultPillHTML()}`;
  }

  /* ── Inject full card HTML ─────────────────────────────────────────────── */
  card.innerHTML = `
    <div class="q-meta">
      <span class="q-num">Вопрос ${state.currentIdx + 1}</span>
      <span class="q-type ${typeCss}">${typeLabel}</span>
      ${diffLabel ? `<span class="q-diff ${diffCss}">${diffLabel}</span>` : ''}
    </div>
    <div class="q-text">${esc(q.text || 'Текст вопроса недоступен')}</div>
    ${answerBody}
  `;

  /* ── NO DIRECT EVENT LISTENERS ON OPTIONS ANYMORE ───────────────────────── */
  /* All option clicks are handled by global delegation in initTestClickHandler() */

  /* ── Bind textarea interactions ────────────────────────────────────────── */
  const textarea = $('#answer-textarea', card);
  if (textarea) {
    const counter = $('#char-count', card);

    const updateCounter = () => {
      if (!counter) return;
      if (q.question_type === 'code') {
        const lines = textarea.value.split('\n').length;
        counter.textContent = `${lines} ${lines === 1 ? 'строка' : 'строк'}`;
      } else {
        counter.textContent = `${textarea.value.length} символов`;
      }
    };
    updateCounter();

    textarea.addEventListener('input', () => {
      if (!state.answers[q.id]) state.answers[q.id] = {};
      state.answers[q.id].answerText = textarea.value;
      updateCounter();
    });

    textarea.addEventListener('blur', () => saveTextAnswer(q));

    // Tab indentation for code
    if (q.question_type === 'code') {
      textarea.addEventListener('keydown', e => {
        if (e.key === 'Tab') {
          e.preventDefault();
          const s = textarea.selectionStart;
          textarea.value = textarea.value.slice(0, s) + '  ' + textarea.value.slice(textarea.selectionEnd);
          textarea.selectionStart = textarea.selectionEnd = s + 2;
          if (!state.answers[q.id]) state.answers[q.id] = {};
          state.answers[q.id].answerText = textarea.value;
        }
      });
    }
  }

  /* ── Copy button for code ──────────────────────────────────────────────── */
  const copyBtn = $('#code-copy-btn', card);
  if (copyBtn && textarea) {
    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(textarea.value);
        copyBtn.textContent = 'Скопировано ✓';
        setTimeout(() => { copyBtn.textContent = 'Копировать'; }, 1800);
      } catch {
        toast('Не удалось скопировать', 'error');
      }
    });
  }

  /* ── Navigation buttons ────────────────────────────────────────────────── */
  const prevBtn = $('#prev-btn');
  const nextBtn = $('#next-btn');

  if (prevBtn) {
    prevBtn.disabled = state.currentIdx === 0;
    const prevNew = prevBtn.cloneNode(true);
    prevBtn.replaceWith(prevNew);
    prevNew.addEventListener('click', () => {
      autoSaveText();
      if (state.currentIdx > 0) {
        state.currentIdx--;
        renderNavDots();
        renderQuestion();
        updateProgress();
      }
    });
  }

  if (nextBtn) {
    const isLast = state.currentIdx === state.questions.length - 1;
    nextBtn.innerHTML = isLast
      ? `<span>Завершить тест</span>${SVG.flag()}`
      : `<span>Далее</span>${SVG.arrowR()}`;

    const nextNew = nextBtn.cloneNode(true);
    nextBtn.replaceWith(nextNew);
    nextNew.addEventListener('click', () => {
      autoSaveText();
      if (isLast) {
        confirmFinish();
      } else {
        state.currentIdx++;
        renderNavDots();
        renderQuestion();
        updateProgress();
      }
    });
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   GLOBAL EVENT DELEGATION FOR OPTIONS (FIXES THE ISSUE)
   ═══════════════════════════════════════════════════════════════════════════ */
function initTestClickHandler() {
  document.addEventListener('click', (e) => {
    // Find the actual option element (either .option itself or a child inside it)
    let optionEl = e.target.closest('.option');
    if (!optionEl) return;

    // Only handle clicks when test screen is active
    const testScreen = $('#screen-test');
    if (!testScreen || !testScreen.classList.contains('active')) return;

    const card = $('#q-card');
    if (!card) return;

    const currentQuestion = state.questions[state.currentIdx];
    if (!currentQuestion) return;

    // Determine if multiple choice
    const isMulti = currentQuestion.question_type === 'multiple_choice';
    const optId = optionEl.dataset.optId;
    if (!optId) return;

    // Get or initialize answer state for this question
    if (!state.answers[currentQuestion.id]) {
      state.answers[currentQuestion.id] = { selectedOptions: [] };
    }
    const ans = state.answers[currentQuestion.id];

    // Update UI and state based on type
    if (isMulti) {
      // Toggle for multiple choice
      const set = new Set(ans.selectedOptions || []);
      if (set.has(optId)) {
        set.delete(optId);
        optionEl.classList.remove('check-selected');
        optionEl.setAttribute('aria-checked', 'false');
      } else {
        set.add(optId);
        optionEl.classList.add('check-selected');
        optionEl.setAttribute('aria-checked', 'true');
      }
      ans.selectedOptions = [...set];
    } else {
      // Single choice: deselect all others, select this one
      const allOptions = $$('.option', card);
      allOptions.forEach(opt => {
        opt.classList.remove('radio-selected');
        opt.setAttribute('aria-checked', 'false');
      });
      optionEl.classList.add('radio-selected');
      optionEl.setAttribute('aria-checked', 'true');
      ans.selectedOptions = [optId];
    }

    // Submit the answer
    autoSubmitChoice(currentQuestion);
  });
}

/* ── Save current text answer to state (called on blur / navigate) ─────────── */
function autoSaveText() {
  const textarea = $('#answer-textarea');
  if (!textarea) return;
  const q = state.questions[state.currentIdx];
  if (!q) return;
  if (!state.answers[q.id]) state.answers[q.id] = {};
  state.answers[q.id].answerText = textarea.value;
  if (textarea.value.trim()) saveTextAnswer(q);
}

/* ── Submit choice answer to API ────────────────────────────────────────────── */
async function autoSubmitChoice(question) {
  const ans = state.answers[question.id];
  if (!ans || state.submitting[question.id]) return;

  state.submitting[question.id] = true;
  try {
    const result = await apiFetch(ENDPOINTS.submitAnswer, {
      method: 'POST',
      body: JSON.stringify({
        attempt_id:       state.attempt.attempt_id,
        question_id:      question.id,
        answer_text:      '',
        selected_options: ans.selectedOptions || [],
      }),
    });
    ans.submitted      = true;
    ans.is_correct     = result.is_correct;
    ans.grading_status = result.grading_status;

    // Update or inject result pill without full re-render
    updateResultPill(result);
    renderNavDots();
    updateProgress();
  } catch (err) {
    toast('Ошибка сохранения: ' + err.message, 'error');
  } finally {
    delete state.submitting[question.id];
  }
}

/* ── Update result pill after submission ────────────────────────────────────── */
function updateResultPill(result) {
  const card = $('#q-card');
  if (!card) return;

  let pill = $('.result-pill', card);
  if (!pill) {
    pill = document.createElement('div');
    card.appendChild(pill);
  }

  if (result.is_correct === true)  { pill.className = 'result-pill pill-correct'; pill.innerHTML = `${SVG.check()} Верно`; }
  else if (result.is_correct === false) { pill.className = 'result-pill pill-wrong'; pill.innerHTML = `${SVG.x()} Неверно`; }
  else                             { pill.className = 'result-pill pill-pending'; pill.innerHTML = `${SVG.clock()} Ожидает проверки`; }
}

/* ── Save text / code answer to API ─────────────────────────────────────────── */
async function saveTextAnswer(question) {
  const ans = state.answers[question.id];
  const text = ans?.answerText?.trim() || '';
  if (!text || state.submitting[question.id]) return;

  state.submitting[question.id] = true;
  try {
    const result = await apiFetch(ENDPOINTS.submitAnswer, {
      method: 'POST',
      body: JSON.stringify({
        attempt_id:       state.attempt.attempt_id,
        question_id:      question.id,
        answer_text:      text,
        selected_options: [],
      }),
    });
    if (!state.answers[question.id]) state.answers[question.id] = {};
    state.answers[question.id].submitted      = true;
    state.answers[question.id].is_correct     = result.is_correct;
    state.answers[question.id].grading_status = result.grading_status;

    updateResultPill(result);
    renderNavDots();
    updateProgress();
  } catch {
    // Silently fail — answer is still in state and will retry
  } finally {
    delete state.submitting[question.id];
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   FINISH FLOW
   ═══════════════════════════════════════════════════════════════════════════ */
function initFinishButton() {
  $('#finish-btn')?.addEventListener('click', confirmFinish);
}

function confirmFinish() {
  const total      = state.questions.length;
  const answered   = Object.values(state.answers).filter(a => a.submitted).length;
  const unanswered = total - answered;

  if (unanswered > 0) {
    const noun = unanswered === 1 ? 'вопрос остался' : `вопросов осталось`;
    if (!confirm(`${unanswered} ${noun} без ответа. Всё равно завершить тест?`)) return;
  }

  doFinish();
}

async function doFinish() {
  stopTimer();
  showLoading('Подводим итоги...');

  try {
    const result = await apiFetch(ENDPOINTS.finish, {
      method: 'POST',
      body: JSON.stringify({ attempt_id: state.attempt.attempt_id }),
    });
    const detail = await apiFetch(ENDPOINTS.result(state.attempt.attempt_id));

    renderResultScreen(result, detail);
    showScreen('screen-result');
  } catch (err) {
    toast('Ошибка завершения: ' + err.message, 'error');
    startTimer();
  } finally {
    hideLoading();
  }
}

/* ═══════════════════════════════════════════════════════════════════════════
   SCREEN 4 — RESULTS
   ═══════════════════════════════════════════════════════════════════════════ */
function renderResultScreen(result, detail) {
  const score  = result.score ?? 0;
  const pass   = score >= 70;
  const ok     = score >= 40;
  const heroClass = pass ? 'hero-pass' : ok ? 'hero-ok' : 'hero-fail';
  const color     = pass ? '#4ECDC4' : ok ? '#FFD166' : '#ef4444';
  const emoji     = pass ? '🎉' : ok ? '👍' : '📚';
  const title     = pass ? 'Отличный результат!' : ok ? 'Неплохо!' : 'Нужна практика';
  const sub       = pass
    ? `Поздравляем, ${esc(result.student_name)}! Тест пройден.`
    : ok
    ? `Хорошая работа, ${esc(result.student_name)}! Есть куда расти.`
    : `Не расстраивайся, ${esc(result.student_name)}. Попробуй ещё раз!`;

  const C = 2 * Math.PI * 54; // circumference
  const offset = C - (score / 100) * C;

  /* ── Hero ───────────────────────────────────────────────────────────────── */
  const hero = $('#result-hero');
  hero.className = `result-hero glass-panel ${heroClass}`;
  hero.innerHTML = `
    <div class="score-ring-wrap">
      <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
        <circle class="ring-track" cx="60" cy="60" r="54"/>
        <circle class="ring-fill" cx="60" cy="60" r="54"
          stroke="${color}"
          stroke-dasharray="${C}"
          stroke-dashoffset="${C}"
          id="ring-fill-el"
        />
      </svg>
      <div class="score-text" style="color:${color};">${Math.round(score)}%</div>
    </div>
    <div class="hero-title">${emoji} ${title}</div>
    <div class="hero-sub">${sub}</div>
  `;

  // Animate ring
  requestAnimationFrame(() => setTimeout(() => {
    const el = $('#ring-fill-el');
    if (el) el.style.strokeDashoffset = offset;
  }, 80));

  /* ── Stats grid ─────────────────────────────────────────────────────────── */
  const duration = result.duration_seconds
    ? `${Math.floor(result.duration_seconds / 60)}м ${Math.round(result.duration_seconds % 60)}с`
    : '—';
  const pending  = result.pending_grading || 0;
  const wrong    = (result.answered || 0) - (result.correct || 0) - pending;

  $('#result-stats').innerHTML = `
    <div class="stat-box"><div class="stat-val sv-green">${result.correct || 0}</div><div class="stat-label">Верных</div></div>
    <div class="stat-box"><div class="stat-val sv-red">${Math.max(0, wrong)}</div><div class="stat-label">Неверных</div></div>
    <div class="stat-box"><div class="stat-val sv-amber">${pending}</div><div class="stat-label">На проверке</div></div>
    <div class="stat-box"><div class="stat-val">${result.answered || 0}</div><div class="stat-label">Отвечено</div></div>
    <div class="stat-box"><div class="stat-val sv-peri">${result.total_questions || 0}</div><div class="stat-label">Всего</div></div>
    <div class="stat-box"><div class="stat-val" style="font-size:20px;">${duration}</div><div class="stat-label">Время</div></div>
  `;

  /* ── Breakdown list ─────────────────────────────────────────────────────── */
  const answers = Array.isArray(detail?.answers) ? detail.answers : [];
  const list    = $('#breakdown-list');

  if (!answers.length) {
    list.innerHTML = `<div class="fallback-state"><p>Данные недоступны</p></div>`;
  } else {
    list.innerHTML = answers.map(a => {
      let iconClass = 'bdi-pending', iconSvg = SVG.clock();
      if (a.is_correct === true)  { iconClass = 'bdi-correct'; iconSvg = SVG.check(); }
      if (a.is_correct === false) { iconClass = 'bdi-wrong';   iconSvg = SVG.x(); }

      let ansPreview = '';
      if (a.answer_text)              ansPreview = truncate(a.answer_text, 80);
      else if (a.selected_options?.length) ansPreview = `${a.selected_options.length} вариант(а/ов)`;

      return `
        <div class="bd-item">
          <div class="bd-icon ${iconClass}">${iconSvg}</div>
          <div class="bd-content">
            <div class="bd-q">${esc(truncate(a.question_text || '—', 110))}</div>
            ${ansPreview ? `<div class="bd-a">${esc(ansPreview)}</div>` : ''}
          </div>
        </div>`;
    }).join('');
  }

  /* ── Restart button ─────────────────────────────────────────────────────── */
  const restartBtn = $('#restart-btn');
  const newRestart = restartBtn.cloneNode(true);
  restartBtn.replaceWith(newRestart);
  newRestart.addEventListener('click', () => {
    Object.assign(state, {
      session: null, attempt: null, questions: [],
      answers: {}, currentIdx: 0, elapsed: 0,
    });
    $('#session-key-input').value  = '';
    $('#student-name-input').value = '';
    showScreen('screen-entry');
    toast('Можете начать заново', 'info');
  });
}

/* ═══════════════════════════════════════════════════════════════════════════
   KEYBOARD SHORTCUTS
   ═══════════════════════════════════════════════════════════════════════════ */
document.addEventListener('keydown', e => {
  const active = document.querySelector('.screen.active');
  if (!active || active.id !== 'screen-test') return;
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;

  const q = state.questions[state.currentIdx];
  if (!q) return;

  // 1-9 selects option
  if (q.question_type === 'single_choice' || q.question_type === 'multiple_choice') {
    const num = parseInt(e.key, 10);
    if (num >= 1 && num <= 9) {
      const opts = $$('.option', $('#q-card'));
      if (opts[num - 1]) opts[num - 1].click();
      return;
    }
  }

  // Arrow keys navigate
  if ((e.key === 'ArrowRight' || e.key === 'ArrowDown') && state.currentIdx < state.questions.length - 1) {
    e.preventDefault();
    autoSaveText();
    state.currentIdx++;
    renderNavDots(); renderQuestion(); updateProgress();
  }
  if ((e.key === 'ArrowLeft' || e.key === 'ArrowUp') && state.currentIdx > 0) {
    e.preventDefault();
    autoSaveText();
    state.currentIdx--;
    renderNavDots(); renderQuestion(); updateProgress();
  }
});

/* ═══════════════════════════════════════════════════════════════════════════
   INIT
   ═══════════════════════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initEntryScreen();
  initNameScreen();
  initFinishButton();
  initTestClickHandler(); // NEW: global event delegation for options

  showScreen('screen-entry');
  $('#session-key-input')?.focus();

  console.info(
    '%c OkurmenKids %c Ready ',
    'background:#FF6B35;color:#fff;font-weight:800;padding:3px 8px;border-radius:4px 0 0 4px;',
    'background:#1e2633;color:#4ECDC4;font-weight:700;padding:3px 8px;border-radius:0 4px 4px 0;',
    '— Shortcuts: 1-9 select option, ← → navigate'
  );
});