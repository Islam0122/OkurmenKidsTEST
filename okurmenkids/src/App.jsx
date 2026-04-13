import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useSessionStore } from './store/sessionStore';
import Layout from './components/Layout';
import EntryPage from './pages/EntryPage';
import DashboardPage from './pages/DashboardPage';
import PreparationPage from './pages/PreparationPage';
import QuestsPage from './pages/QuestsPage';
import StoriesPage from './pages/StoriesPage';
import BadgesPage from './pages/BadgesPage';
import ExamPage from './pages/ExamPage';

function ProtectedRoute({ children }) {
  const { studentName } = useSessionStore();
  if (!studentName) return <Navigate to="/" replace />;
  return children;
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

function AppRoutes() {
  const { studentName } = useSessionStore();
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={studentName ? <Navigate to="/dashboard" replace /> : <EntryPage />} />
        <Route path="/dashboard" element={<ProtectedRoute><Layout><DashboardPage /></Layout></ProtectedRoute>} />
        <Route path="/preparation" element={<ProtectedRoute><Layout><PreparationPage /></Layout></ProtectedRoute>} />
        <Route path="/quests" element={<ProtectedRoute><Layout><QuestsPage /></Layout></ProtectedRoute>} />
        <Route path="/stories" element={<ProtectedRoute><Layout><StoriesPage /></Layout></ProtectedRoute>} />
        <Route path="/badges" element={<ProtectedRoute><Layout><BadgesPage /></Layout></ProtectedRoute>} />
        <Route path="/exam" element={<ProtectedRoute><Layout><ExamPage /></Layout></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
