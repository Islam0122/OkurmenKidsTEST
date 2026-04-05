/**
 * OkurmenKids Frontend — app.js
 * Vanilla JS, async/await, no dependencies
 */

'use strict';

/* ═══════════════════════════════════════════════════════════
   CONFIG
   ═══════════════════════════════════════════════════════════ */
const BASE_URL = 'https://okurmenkidstest.up.railway.app';

const API = {
  validateSession: (key)        => `${BASE_URL}/api/v1/sessions/validate`,
  startAttempt:   ()            => `${BASE_URL}/api/v1/attempt/start`,
  submitAnswer:   ()            => `${BASE_URL}/api/v1/attempt/answer`,
  finishAttempt:  ()            => `${BASE_URL}/api/v1/attempt/finish`,
  getResult:      (id)          => `${BASE_URL}/api/v1/attempt/${id}/result`,
};

/* ═══════════════════════════════════════════════════════════
   STATE
   ═══════════════════════════════════════════════════════════ */
const state = {
  session:      null,   // session data from API
  attempt:      null,   // attempt data from API
  questions:    [],     // list of questions
  currentIdx:   0,      // current question index
  answers:      {},     // { questionId: { text?, selectedOptions?, submitted, is_correct, grading_status } }
  timerInterval: null,
  elapsedSecs:  0,
  submitting:   {},     // { questionId: Promise } to avoid double-submit
};

/* ═══════════════════════════════════════════════════════════
   UTILITIES
   ═══════════════════════════════════════════════════════════ */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => ctx.querySelectorAll(sel);

function showScreen(id) {
  $$('.screen').forEach(s => {
    s.classList.remove('active');
    s.style.display = '';
  });
  const scr = $(`#${id}`);
  if (scr) {
    scr.classList.add('active');
    // Force animation restart
    scr.style.animation = 'none';
    scr.offsetHeight;
    scr.style.animation = '';
  }
}

function showLoading(text = 'Загрузка...') {
  const el = $('#screen-loading');
  el.classList.remove('hidden');
  $('#loading-text').textContent = text;
}

function hideLoading() {
  $('#screen-loading').classList.add('hidden');
}

/* ── Toast ─────────────────────────────────────────────────────────────────── */
function toast(message, type = 'info', duration = 3500) {
  const container = $('#toast-container');
  const icons = {
    success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
    error:   `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
    info:    `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>`,
    warning: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
  };
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `${icons[type] || icons.info}<span>${escapeHtml(message)}</span>`;
  container.appendChild(el);
  setTimeout(() => {
    el.classList.add('out');
    el.addEventListener('animationend', () => el.remove(), { once: true });
  }, duration);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── HTTP ────────────────────────────────────────────────────────────────── */
async function apiFetch(url, options = {}) {
  const defaults = {
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
  };
  const config = {
    ...defaults,
    ...options,
    headers: { ...defaults.headers, ...(options.headers || {}) },
  };
  const res = await fetch(url, config);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.detail || data.message || `Ошибка ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

/* ═══════════════════════════════════════════════════════════
   TIMER
   ═══════════════════════════════════════════════════════════ */
function startTimer() {
  state.elapsedSecs = 0;
  clearInterval(state.timerInterval);
  state.timerInterval = setInterval(() => {
    state.elapsedSecs++;
    renderTimer();
  }, 1000);
}

function stopTimer() {
  clearInterval(state.timerInterval);
  state.timerInterval = null;
}

function renderTimer() {
  const el = $('#timer-value');
  const disp = $('#timer-display');
  if (!el) return;
  const m = Math.floor(state.elapsedSecs / 60).toString().padStart(2, '0');
  const s = (state.elapsedSecs % 60).toString().padStart(2, '0');
  el.textContent = `${m}:${s}`;

  // Exam sessions: warn if elapsed > (expires_at - now) * 0.8
  if (state.session?.session_type === 'exam' && state.session?.expires_at) {
    const expiresAt = new Date(state.session.expires_at);
    const totalSecs = (expiresAt - new Date()) / 1000;
    if (totalSecs < 300) disp.classList.add('urgent');
    else disp.classList.remove('urgent');
  }
}

/* ═══════════════════════════════════════════════════════════
   SCREEN 1: SESSION ENTRY
   ═══════════════════════════════════════════════════════════ */
function initEntryScreen() {
  const input  = $('#session-key-input');
  const btn    = $('#validate-btn');

  // Enter key submit
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') btn.click();
  });

  btn.addEventListener('click', async () => {
    const key = input.value.trim();
    if (!key) { toast('Введите ключ сессии', 'warning'); input.focus(); return; }

    btn.disabled = true;
    btn.querySelector('.btn-text').textContent = 'Проверяем...';
    showLoading('Проверяем ключ сессии...');

    try {
      const session = await apiFetch(API.validateSession(), {
        method: 'POST',
        body: JSON.stringify({ key }),
      });
      state.session = session;
      renderSessionInfo(session);
      showScreen('screen-name');
      $('#student-name-input').focus();
      toast('Сессия найдена!', 'success');
    } catch (err) {
      toast(err.message || 'Неверный ключ сессии', 'error');
    } finally {
      hideLoading();
      btn.disabled = false;
      btn.querySelector('.btn-text').textContent = 'Проверить ключ';
    }
  });

  // Paste auto-submit
  input.addEventListener('paste', () => {
    setTimeout(() => {
      if (input.value.trim().length >= 10) btn.click();
    }, 100);
  });
}

/* ═══════════════════════════════════════════════════════════
   SCREEN 2: NAME + SESSION INFO
   ═══════════════════════════════════════════════════════════ */
function renderSessionInfo(session) {
  const card = $('#session-info-display');
  const typeClass = session.session_type === 'exam' ? 'badge-exam' : 'badge-training';
  const typeName  = session.session_type === 'exam' ? 'Экзамен' : 'Тренажёр';
  const validBadge = session.is_valid
    ? '<span class="badge-type badge-active">Активна</span>'
    : '<span class="badge-type badge-inactive">Истекла</span>';

  let expiresRow = '';
  if (session.session_type === 'exam' && session.expires_at) {
    const exp = new Date(session.expires_at);
    expiresRow = `
      <div class="si-row">
        <span class="si-key">Истекает</span>
        <span class="si-val">${exp.toLocaleString('ru', { hour:'2-digit', minute:'2-digit', day:'numeric', month:'short' })}</span>
      </div>`;
  }

  card.innerHTML = `
    <div class="si-row">
      <span class="si-key">Тест</span>
      <span class="si-val">${escapeHtml(session.test_title || '—')}</span>
    </div>
    <div class="si-row">
      <span class="si-key">Тип</span>
      <span class="si-val"><span class="badge-type ${typeClass}">${typeName}</span></span>
    </div>
    <div class="si-row">
      <span class="si-key">Статус</span>
      <span class="si-val">${validBadge}</span>
    </div>
    ${expiresRow}
    ${session.title ? `<div class="si-row"><span class="si-key">Название</span><span class="si-val">${escapeHtml(session.title)}</span></div>` : ''}
  `;
}

function initNameScreen() {
  $('#back-to-entry').addEventListener('click', () => {
    state.session = null;
    showScreen('screen-entry');
    $('#session-key-input').focus();
  });

  const nameInput = $('#student-name-input');
  const startBtn  = $('#start-attempt-btn');

  nameInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') startBtn.click();
  });

  startBtn.addEventListener('click', async () => {
    const name = nameInput.value.trim();
    if (!name) { toast('Введите ваше имя', 'warning'); nameInput.focus(); return; }
    if (name.length < 2) { toast('Имя слишком короткое', 'warning'); return; }

    startBtn.disabled = true;
    startBtn.querySelector('.btn-text').textContent = 'Запускаем...';
    showLoading('Начинаем тест...');

    try {
      const attempt = await apiFetch(API.startAttempt(), {
        method: 'POST',
        body: JSON.stringify({ key: state.session.key, student_name: name }),
      });
      state.attempt   = attempt;
      state.questions = attempt.questions || [];
      state.answers   = {};
      state.currentIdx = 0;

      if (!state.questions.length) {
        toast('В этом тесте нет вопросов', 'warning');
        return;
      }

      renderTestScreen();
      showScreen('screen-test');
      startTimer();
      toast('Тест начат! Удачи 🎯', 'success');
    } catch (err) {
      toast(err.message || 'Не удалось начать тест', 'error');
    } finally {
      hideLoading();
      startBtn.disabled = false;
      startBtn.querySelector('.btn-text').textContent = 'Начать тест';
    }
  });
}

/* ═══════════════════════════════════════════════════════════
   SCREEN 3: TEST
   ═══════════════════════════════════════════════════════════ */
function renderTestScreen() {
  // Header
  $('#hdr-test-title').textContent  = state.attempt.test_title || '—';
  $('#hdr-student-name').textContent = state.attempt.student_name || '—';

  renderQuestionNav();
  renderCurrentQuestion();
  updateProgress();
}

function renderQuestionNav() {
  const nav = $('#question-nav');
  nav.innerHTML = state.questions.map((q, i) => {
    const ans = state.answers[q.id];
    const answered = ans && ans.submitted;
    const current  = i === state.currentIdx;
    return `<button class="q-dot ${answered ? 'answered' : ''} ${current ? 'current' : ''}" data-idx="${i}" title="Вопрос ${i + 1}">${i + 1}</button>`;
  }).join('');

  nav.querySelectorAll('.q-dot').forEach(dot => {
    dot.addEventListener('click', () => {
      state.currentIdx = parseInt(dot.dataset.idx, 10);
      renderCurrentQuestion();
      renderQuestionNav();
      updateProgress();
    });
  });
}

function updateProgress() {
  const total    = state.questions.length;
  const answered = Object.values(state.answers).filter(a => a.submitted).length;
  const pct      = total ? (answered / total) * 100 : 0;
  $('#progress-fill').style.width = `${pct}%`;
  $('#progress-label').textContent = `${answered} / ${total}`;
}

function renderCurrentQuestion() {
  const q   = state.questions[state.currentIdx];
  const ans = state.answers[q.id] || {};
  const card = $('#question-card');

  const typeLabels = { single_choice: 'Один ответ', multiple_choice: 'Несколько', text: 'Текст', code: 'Код' };
  const typeClasses = { single_choice: 'qt-single', multiple_choice: 'qt-multiple', text: 'qt-text', code: 'qt-code' };
  const diffLabels  = { easy: 'Лёгкий', medium: 'Средний', hard: 'Сложный' };
  const diffClasses = { easy: 'diff-easy', medium: 'diff-medium', hard: 'diff-hard' };

  // Build answer result pill
  let resultPill = '';
  if (ans.submitted) {
    if (ans.is_correct === true)  resultPill = `<div class="answer-result-pill correct">${svgCheck()} Верно</div>`;
    if (ans.is_correct === false) resultPill = `<div class="answer-result-pill wrong">${svgX()} Неверно</div>`;
    if (ans.is_correct === null)  resultPill = `<div class="answer-result-pill pending">${svgClock()} Будет проверено позже</div>`;
  }

  let body = '';
  if (q.question_type === 'single_choice' || q.question_type === 'multiple_choice') {
    const opts = (q.options || []);
    const isMulti = q.question_type === 'multiple_choice';
    const selected = new Set(ans.selectedOptions || []);
    const letters  = 'ABCDEFGHIJ';

    body = `
      ${isMulti ? `<p style="font-size:12px;color:var(--text-muted);margin-bottom:14px;"><svg style="width:12px;height:12px;vertical-align:middle;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12l2 2 4-4"/></svg> Можно выбрать несколько вариантов</p>` : ''}
      <div class="options-list">
        ${opts.map((opt, i) => `
          <div class="option-item ${isMulti ? 'multi' : ''} ${selected.has(opt.id) ? 'selected' : ''}"
               data-opt-id="${opt.id}"
               role="${isMulti ? 'checkbox' : 'radio'}"
               aria-checked="${selected.has(opt.id)}"
               tabindex="0">
            <div class="option-marker">
              <span class="letter-lbl">${letters[i] || i + 1}</span>
              <svg class="check-icon" style="width:12px;height:12px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
            </div>
            <div class="option-text">${escapeHtml(opt.text)}</div>
          </div>
        `).join('')}
      </div>
      ${resultPill}
    `;
  } else {
    // text or code
    const isCode = q.question_type === 'code';
    const langHint = isCode && q.language ? `
      <div class="code-lang-hint">
        <svg style="width:12px;height:12px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
        <span class="code-lang-badge">${q.language}</span>
      </div>` : '';

    body = `
      ${langHint}
      <textarea
        class="text-answer-area ${isCode ? 'code-mode' : ''}"
        placeholder="${isCode ? `// Введите код на ${q.language || 'коде'}...` : 'Введите ваш ответ...'}"
        id="text-answer-textarea"
        rows="6"
      >${escapeHtml(ans.answerText || '')}</textarea>
      <div class="submit-hint">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        Ответ сохраняется автоматически при переходе
      </div>
      ${resultPill}
    `;
  }

  card.innerHTML = `
    <div class="q-meta">
      <span class="q-number-badge">Вопрос ${state.currentIdx + 1}</span>
      <span class="q-type-badge ${typeClasses[q.question_type] || ''}">${typeLabels[q.question_type] || q.question_type}</span>
      <span class="q-difficulty ${diffClasses[q.difficulty] || ''}">${diffLabels[q.difficulty] || q.difficulty}</span>
    </div>
    <div class="q-text">${escapeHtml(q.text)}</div>
    ${body}
  `;

  // Bind option clicks
  if (q.question_type === 'single_choice' || q.question_type === 'multiple_choice') {
    const isMulti = q.question_type === 'multiple_choice';
    card.querySelectorAll('.option-item').forEach(item => {
      const handler = () => handleOptionClick(item, q, isMulti);
      item.addEventListener('click', handler);
      item.addEventListener('keydown', e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); handler(); } });
    });
  }

  // Textarea auto-save on blur/change
  const textarea = $('#text-answer-textarea');
  if (textarea) {
    textarea.addEventListener('blur', () => saveTextAnswer(q));
    textarea.addEventListener('input', () => {
      // Mark as dirty
      if (!state.answers[q.id]) state.answers[q.id] = {};
      state.answers[q.id].answerText = textarea.value;
    });
  }

  // Nav buttons
  const prevBtn = $('#prev-btn');
  const nextBtn = $('#next-btn');
  prevBtn.disabled = state.currentIdx === 0;
  const isLast = state.currentIdx === state.questions.length - 1;
  nextBtn.innerHTML = isLast
    ? `Завершить ${svgFlag()}`
    : `Далее ${svgArrowRight()}`;

  // Cleanup old listeners by replacing buttons (clone trick)
  replaceWithClone(prevBtn, () => {
    if (textarea) saveTextAnswer(q);
    if (state.currentIdx > 0) {
      state.currentIdx--;
      renderCurrentQuestion();
      renderQuestionNav();
    }
  });
  replaceWithClone(nextBtn, () => {
    if (textarea) saveTextAnswer(q);
    if (isLast) {
      confirmFinish();
    } else {
      state.currentIdx++;
      renderCurrentQuestion();
      renderQuestionNav();
    }
  });
}

function replaceWithClone(btn, handler) {
  const newBtn = btn.cloneNode(true);
  btn.parentNode.replaceChild(newBtn, btn);
  newBtn.addEventListener('click', handler);
}

function handleOptionClick(item, question, isMulti) {
  const optId = item.dataset.optId;
  if (!state.answers[question.id]) state.answers[question.id] = { selectedOptions: [] };
  const ans = state.answers[question.id];

  if (isMulti) {
    const set = new Set(ans.selectedOptions || []);
    if (set.has(optId)) {
      set.delete(optId);
      item.classList.remove('selected');
    } else {
      set.add(optId);
      item.classList.add('selected');
    }
    ans.selectedOptions = [...set];
  } else {
    // Single: deselect all, select this
    $('#question-card').querySelectorAll('.option-item').forEach(i => i.classList.remove('selected'));
    item.classList.add('selected');
    ans.selectedOptions = [optId];
  }

  item.setAttribute('aria-checked', item.classList.contains('selected'));
  autoSubmitAnswer(question);
}

async function autoSubmitAnswer(question) {
  const ans = state.answers[question.id];
  if (!ans) return;

  // Prevent double submit
  if (state.submitting[question.id]) return;

  const payload = {
    attempt_id:       state.attempt.attempt_id,
    question_id:      question.id,
    answer_text:      ans.answerText || '',
    selected_options: ans.selectedOptions || [],
  };

  // Mark optimistically
  state.submitting[question.id] = true;

  try {
    const result = await apiFetch(API.submitAnswer(), {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    ans.submitted      = true;
    ans.is_correct     = result.is_correct;
    ans.grading_status = result.grading_status;

    // Show inline result
    const pill = $('#question-card .answer-result-pill');
    if (pill) {
      if (result.is_correct === true)  { pill.className = 'answer-result-pill correct'; pill.innerHTML = `${svgCheck()} Верно`; }
      if (result.is_correct === false) { pill.className = 'answer-result-pill wrong';   pill.innerHTML = `${svgX()} Неверно`; }
      if (result.is_correct === null)  { pill.className = 'answer-result-pill pending'; pill.innerHTML = `${svgClock()} Будет проверено позже`; }
    } else {
      // Insert pill
      const card = $('#question-card');
      const newPill = document.createElement('div');
      if (result.is_correct === true)  { newPill.className = 'answer-result-pill correct'; newPill.innerHTML = `${svgCheck()} Верно`; }
      if (result.is_correct === false) { newPill.className = 'answer-result-pill wrong';   newPill.innerHTML = `${svgX()} Неверно`; }
      if (result.is_correct === null)  { newPill.className = 'answer-result-pill pending'; newPill.innerHTML = `${svgClock()} Будет проверено позже`; }
      card.appendChild(newPill);
    }

    renderQuestionNav();
    updateProgress();
  } catch (err) {
    toast('Ошибка сохранения ответа: ' + err.message, 'error');
  } finally {
    delete state.submitting[question.id];
  }
}

async function saveTextAnswer(question) {
  const textarea = $('#text-answer-textarea');
  if (!textarea) return;
  const text = textarea.value.trim();
  if (!text) return;

  if (!state.answers[question.id]) state.answers[question.id] = {};
  state.answers[question.id].answerText = text;
  await autoSubmitAnswer(question);
}

/* ── Finish ─────────────────────────────────────────────────────────────── */
function initFinishButton() {
  $('#finish-btn').addEventListener('click', confirmFinish);
}

function confirmFinish() {
  const answered = Object.values(state.answers).filter(a => a.submitted).length;
  const total    = state.questions.length;
  const unanswered = total - answered;

  if (unanswered > 0) {
    const msg = unanswered === 1
      ? `Остался 1 вопрос без ответа. Завершить тест?`
      : `Осталось ${unanswered} вопросов без ответа. Завершить тест?`;

    // Inline confirm with toast-like modal
    if (!confirm(msg)) return;
  }

  doFinish();
}

async function doFinish() {
  stopTimer();
  showLoading('Подводим итоги...');

  try {
    const result = await apiFetch(API.finishAttempt(), {
      method: 'POST',
      body: JSON.stringify({ attempt_id: state.attempt.attempt_id }),
    });

    // Fetch detailed result
    const detail = await apiFetch(API.getResult(state.attempt.attempt_id));
    renderResultScreen(result, detail);
    showScreen('screen-result');
  } catch (err) {
    toast('Ошибка завершения: ' + err.message, 'error');
    startTimer(); // Resume if failed
  } finally {
    hideLoading();
  }
}

/* ═══════════════════════════════════════════════════════════
   SCREEN 4: RESULTS
   ═══════════════════════════════════════════════════════════ */
function renderResultScreen(result, detail) {
  const score = result.score || 0;
  const pass  = score >= 70;
  const mid   = score >= 40;

  // Hero
  const heroClass = pass ? 'pass' : mid ? 'ok' : 'fail';
  const color     = pass ? '#10b981' : mid ? '#f59e0b' : '#ef4444';
  const title     = pass ? '🎉 Отличный результат!' : mid ? '👍 Неплохо!' : '📚 Нужна практика';
  const subtitle  = pass
    ? `Поздравляем, ${escapeHtml(result.student_name)}! Тест пройден успешно.`
    : mid
    ? `Хороший результат, ${escapeHtml(result.student_name)}. Есть куда расти!`
    : `Не расстраивайся, ${escapeHtml(result.student_name)}. Попробуй ещё раз!`;

  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;

  $('#result-hero').className = `result-hero ${heroClass}`;
  $('#result-hero').innerHTML = `
    <div class="score-ring">
      <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
        <circle class="score-ring-track" cx="60" cy="60" r="54"/>
        <circle class="score-ring-fill"
          cx="60" cy="60" r="54"
          stroke="${color}"
          stroke-dasharray="${circumference}"
          stroke-dashoffset="${circumference}"
          id="score-ring-fill-el"
        />
      </svg>
      <div class="score-num" style="color:${color};">${Math.round(score)}%</div>
    </div>
    <div class="result-title">${title}</div>
    <div class="result-subtitle">${subtitle}</div>
  `;

  // Animate ring
  requestAnimationFrame(() => {
    setTimeout(() => {
      const el = $('#score-ring-fill-el');
      if (el) el.style.strokeDashoffset = offset;
    }, 100);
  });

  // Stats grid
  const duration = result.duration_seconds
    ? `${Math.floor(result.duration_seconds / 60)}м ${Math.round(result.duration_seconds % 60)}с`
    : '—';
  const pending = result.pending_grading || 0;

  $('#result-stats-grid').innerHTML = `
    <div class="stat-card">
      <div class="stat-val text-green">${result.correct || 0}</div>
      <div class="stat-lbl">Верных</div>
    </div>
    <div class="stat-card">
      <div class="stat-val" style="color:var(--red);">${(result.answered || 0) - (result.correct || 0) - pending}</div>
      <div class="stat-lbl">Неверных</div>
    </div>
    <div class="stat-card">
      <div class="stat-val text-amber">${pending}</div>
      <div class="stat-lbl">На проверке</div>
    </div>
    <div class="stat-card">
      <div class="stat-val">${result.answered || 0}</div>
      <div class="stat-lbl">Отвечено</div>
    </div>
    <div class="stat-card">
      <div class="stat-val text-muted">${result.total_questions || 0}</div>
      <div class="stat-lbl">Всего</div>
    </div>
    <div class="stat-card">
      <div class="stat-val" style="font-size:18px;">${duration}</div>
      <div class="stat-lbl">Время</div>
    </div>
  `;

  // Answer review
  const answers = detail?.answers || [];
  const raHtml = answers.map(a => {
    let iconCls = 'pending', iconSvg = svgClock();
    if (a.is_correct === true)  { iconCls = 'correct'; iconSvg = svgCheck(); }
    if (a.is_correct === false) { iconCls = 'wrong';   iconSvg = svgX(); }

    let answerPreview = '';
    if (a.answer_text) answerPreview = truncate(a.answer_text, 80);
    else if (a.selected_options?.length) answerPreview = `${a.selected_options.length} вариант(а/ов)`;

    return `
      <div class="result-answer-item">
        <div class="ra-icon ${iconCls}">${iconSvg}</div>
        <div class="ra-content">
          <div class="ra-question">${escapeHtml(truncate(a.question_text || '—', 100))}</div>
          ${answerPreview ? `<div class="ra-answer">${escapeHtml(answerPreview)}</div>` : ''}
        </div>
      </div>
    `;
  }).join('');

  $('#result-answers').innerHTML = `
    <div class="result-answers-header">Детали по вопросам</div>
    ${raHtml || `<div class="empty-state" style="padding:32px;"><p>Нет данных</p></div>`}
  `;

  // Restart button
  replaceWithClone($('#restart-btn'), () => {
    state.session = null;
    state.attempt = null;
    state.questions = [];
    state.answers = {};
    $('#session-key-input').value = '';
    $('#student-name-input').value = '';
    showScreen('screen-entry');
    toast('Можете начать новую попытку', 'info');
  });
}

/* ═══════════════════════════════════════════════════════════
   SVG HELPERS
   ═══════════════════════════════════════════════════════════ */
function svgCheck() {
  return `<svg style="width:14px;height:14px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>`;
}
function svgX() {
  return `<svg style="width:14px;height:14px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
}
function svgClock() {
  return `<svg style="width:14px;height:14px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>`;
}
function svgArrowRight() {
  return `<svg style="width:16px;height:16px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>`;
}
function svgFlag() {
  return `<svg style="width:16px;height:16px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>`;
}

function truncate(str, len) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '…' : str;
}

/* ═══════════════════════════════════════════════════════════
   KEYBOARD SHORTCUTS
   ═══════════════════════════════════════════════════════════ */
document.addEventListener('keydown', e => {
  const screen = document.querySelector('.screen.active');
  if (!screen || screen.id !== 'screen-test') return;
  if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;

  const q = state.questions[state.currentIdx];
  if (!q) return;

  // 1-9: select option
  if (q.question_type === 'single_choice' || q.question_type === 'multiple_choice') {
    const num = parseInt(e.key, 10);
    if (num >= 1 && num <= 9) {
      const opts = document.querySelectorAll('.option-item');
      if (opts[num - 1]) opts[num - 1].click();
    }
  }

  // ArrowLeft/ArrowRight: nav
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
    e.preventDefault();
    if (state.currentIdx < state.questions.length - 1) {
      state.currentIdx++;
      renderCurrentQuestion();
      renderQuestionNav();
    }
  }
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
    e.preventDefault();
    if (state.currentIdx > 0) {
      state.currentIdx--;
      renderCurrentQuestion();
      renderQuestionNav();
    }
  }
});

/* ═══════════════════════════════════════════════════════════
   INIT
   ═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  initEntryScreen();
  initNameScreen();
  initFinishButton();

  // Show entry screen
  showScreen('screen-entry');
  $('#session-key-input').focus();

  // Log keyboard hints
  console.info('%c OkurmenKids ', 'background:#f59e0b;color:#0d1117;font-weight:800;padding:4px 8px;border-radius:4px;', '— Keyboard: 1-9 выбор ответа, ←→ навигация');
});