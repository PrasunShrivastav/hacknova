import React from 'react';
import SearchBar from '../components/SearchBar';
import AgentStatusFeed from '../components/AgentStatusFeed';
import useAriaStore from '../store/useAriaStore';

export default function HomePage() {
  const status = useAriaStore((s) => s.status);
  const error = useAriaStore((s) => s.error);

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
