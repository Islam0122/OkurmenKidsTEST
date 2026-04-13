import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useProgressStore = create(
  persist(
    (set, get) => ({
      completedLessons: [],
      completedQuests: [],
      readStories: [],
      badges: [],
      scores: {},
      xp: 0,
      level: 1,
      streak: 0,
      lastActive: null,

      completeLesson: (id) => {
        const { completedLessons, xp } = get();
        if (!completedLessons.includes(id)) {
          set({ completedLessons: [...completedLessons, id], xp: xp + 20 });
          get().checkBadges();
        }
      },

      completeQuest: (id, score) => {
        const { completedQuests, scores, xp } = get();
        const prev = scores[id] || 0;
        set({
          completedQuests: completedQuests.includes(id) ? completedQuests : [...completedQuests, id],
          scores: { ...scores, [id]: Math.max(prev, score) },
          xp: xp + (score >= 80 ? 50 : score >= 50 ? 30 : 10),
        });
        get().checkBadges();
      },

      readStory: (id) => {
        const { readStories, xp } = get();
        if (!readStories.includes(id)) {
          set({ readStories: [...readStories, id], xp: xp + 15 });
          get().checkBadges();
        }
      },

      earnBadge: (badge) => {
        const { badges } = get();
        if (!badges.find(b => b.id === badge.id)) {
          set({ badges: [...badges, { ...badge, earnedAt: new Date().toISOString() }] });
        }
      },

      checkBadges: () => {
        const { completedLessons, completedQuests, readStories, badges, xp } = get();
        const BADGES = [
          { id: 'first_lesson', label: 'First Steps', icon: '🌱', condition: () => completedLessons.length >= 1, color: '#4ade80' },
          { id: 'lesson_5', label: 'Scholar', icon: '📚', condition: () => completedLessons.length >= 5, color: '#38bdf8' },
          { id: 'first_quest', label: 'Quest Starter', icon: '⚔️', condition: () => completedQuests.length >= 1, color: '#fbbf24' },
          { id: 'quest_master', label: 'Quest Master', icon: '🏆', condition: () => completedQuests.length >= 5, color: '#a78bfa' },
          { id: 'reader', label: 'Book Worm', icon: '🐛', condition: () => readStories.length >= 3, color: '#fb7185' },
          { id: 'xp_100', label: 'Rising Star', icon: '⭐', condition: () => xp >= 100, color: '#fbbf24' },
          { id: 'xp_500', label: 'Code Wizard', icon: '🧙', condition: () => xp >= 500, color: '#a78bfa' },
        ];
        BADGES.forEach(b => {
          if (!badges.find(eb => eb.id === b.id) && b.condition()) {
            get().earnBadge(b);
          }
        });
        // Update level
        const newXp = get().xp;
        const newLevel = Math.floor(newXp / 100) + 1;
        set({ level: newLevel });
      },

      getLessonProgress: (totalLessons) => {
        return Math.round((get().completedLessons.length / totalLessons) * 100);
      },
    }),
    { name: 'okids-progress' }
  )
);
