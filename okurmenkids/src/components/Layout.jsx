import React from 'react';
import Navbar from './Navbar';

export default function Layout({ children }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Navbar />
      {/* Desktop: offset by sidebar width */}
      <main style={{ flex: 1, minHeight: '100vh' }} className="main-content">
        {children}
      </main>
      <style>{`
        @media (min-width: 768px) {
          .main-content { margin-left: 220px; }
        }
        @media (max-width: 767px) {
          .main-content { margin-top: 56px; }
        }
      `}</style>
    </div>
  );
}
