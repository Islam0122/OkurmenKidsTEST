import axios from 'axios';

const BASE = 'https://okurmenkidstest.up.railway.app';

const api = axios.create({
  baseURL: BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// ── Sessions ──────────────────────────────────────────────────────────────────
export const validateSession = (key) =>
  api.post('/api/v1/sessions/validate', { key }).then(r => r.data);

export const enterSession = (key) =>
  api.post('/api/v1/sessions/enter', { key }).then(r => r.data);

// ── Attempts ──────────────────────────────────────────────────────────────────
export const startAttempt = (key, student_name) =>
  api.post('/api/v1/attempt/start', { key, student_name }).then(r => r.data);

export const submitAnswer = (attempt_id, question_id, answer_text, selected_options) =>
  api.post('/api/v1/attempt/answer', { attempt_id, question_id, answer_text, selected_options }).then(r => r.data);

export const finishAttempt = (attempt_id) =>
  api.post('/api/v1/attempt/finish', { attempt_id }).then(r => r.data);

export const getAttemptResult = (attempt_id) =>
  api.get(`/api/v1/attempt/${attempt_id}/result`).then(r => r.data);

// ── Tests ──────────────────────────────────────────────────────────────────────
export const getTests = () =>
  api.get('/api/v1/tests/').then(r => r.data);

export default api;
