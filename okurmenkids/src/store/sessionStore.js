import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useSessionStore = create(
  persist(
    (set, get) => ({
      studentName: '',
      sessionKey: '',
      attemptId: '',
      currentSession: null,

      setStudent: (name) => set({ studentName: name }),
      setSessionKey: (key) => set({ sessionKey: key }),
      setAttemptId: (id) => set({ attemptId: id }),
      setCurrentSession: (session) => set({ currentSession: session }),

      clearExam: () => set({ sessionKey: '', attemptId: '', currentSession: null }),
      clearAll: () => set({ studentName: '', sessionKey: '', attemptId: '', currentSession: null }),
    }),
    { name: 'okids-session' }
  )
);
