import React, { useEffect } from 'react';
import SearchBar from '../components/SearchBar';
import AgentStatusFeed from '../components/AgentStatusFeed';
import SessionHistory from '../components/SessionHistory';
import useAriaStore from '../store/useAriaStore';

export default function HomePage() {
  const status = useAriaStore((s) => s.status);
  const error = useAriaStore((s) => s.error);
  const sessionHistory = useAriaStore((s) => s.sessionHistory);
  const toggleHistory = useAriaStore((s) => s.toggleHistory);
  const loadSessionHistory = useAriaStore((s) => s.loadSessionHistory);

  // Load session history on component mount
  useEffect(() => {
    loadSessionHistory();
  }, [loadSessionHistory]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      {/* Hero section */}
      <div className="text-center mb-10 animate-fade-in">
        {/* Logo */}
        <div className="mb-6 relative inline-block">
          <div className="absolute inset-0 bg-aria-accent/20 rounded-full blur-2xl animate-pulse-slow" />
          <div className="relative text-6xl">🔬</div>
        </div>

        <h1 className="text-5xl font-extrabold tracking-tight mb-3">
          <span className="gradient-text">ARIA</span>
        </h1>
        <p className="text-lg text-aria-text-dim mb-1">
          Autonomous Research Intelligence Agent
        </p>
        <p className="text-sm text-aria-text-muted max-w-lg mx-auto">
          Enter a research question. ARIA will crawl arXiv, Semantic Scholar, and PubMed —
          then extract claims, build a knowledge graph, and synthesize a literature review.
        </p>
      </div>

      {/* Search */}
      <SearchBar />

      {/* History button */}
      {sessionHistory.length > 0 && (
        <div className="mt-6 animate-fade-in">
          <button
            onClick={toggleHistory}
            className="flex items-center gap-2 px-4 py-2 bg-aria-surface/50 border border-aria-border rounded-lg text-sm text-aria-text hover:bg-aria-surface/70 transition-all group"
          >
            <span className="text-lg">📚</span>
            <span>View Session History</span>
            <span className="text-xs bg-aria-accent/10 text-aria-accent px-2 py-0.5 rounded-full">
              {sessionHistory.length}
            </span>
            <span className="text-aria-text-muted group-hover:text-aria-text transition-colors">
              →
            </span>
          </button>
        </div>
      )}

      {/* Status feed during loading */}
      {(status === 'running' || status === 'searching') && (
        <div className="w-full max-w-3xl mt-8 animate-fade-in">
          <AgentStatusFeed />
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="w-full max-w-3xl mt-6 glass-card border-aria-red/30 p-4 animate-slide-up">
          <div className="flex items-start gap-2">
            <span className="text-aria-red">❌</span>
            <div>
              <p className="text-sm font-medium text-aria-red">Research Failed</p>
              <p className="text-xs text-aria-text-dim mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Session History Modal */}
      <SessionHistory />

      {/* Footer stats */}
      <div className="fixed bottom-0 w-full py-4 text-center border-t border-aria-border/30 bg-aria-bg/80 backdrop-blur-sm">
        <div className="flex items-center justify-center gap-6 text-[10px] text-aria-text-muted">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-aria-green" />
            Ollama Local LLM
          </span>
          <span>arXiv · Semantic Scholar · PubMed</span>
          <span>100% Free Stack</span>
        </div>
      </div>
    </div>
  );
}
