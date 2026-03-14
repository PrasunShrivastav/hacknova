import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ResultsPage from './pages/ResultsPage';
import useAriaStore from './store/useAriaStore';

export default function App() {
  const status = useAriaStore((s) => s.status);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-aria-bg">
        {/* Ambient background gradient */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-aria-accent/5 rounded-full blur-3xl" />
          <div className="absolute top-1/3 -left-40 w-80 h-80 bg-aria-purple/5 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 right-1/3 w-72 h-72 bg-aria-amber/5 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10">
          <Routes>
            <Route
              path="/"
              element={
                status === 'idle' || status === 'searching'
                  ? <HomePage />
                  : <ResultsPage />
              }
            />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
