import React, { useState } from 'react';
import useAriaStore from '../store/useAriaStore';

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const [maxPapers, setMaxPapers] = useState(30);
  const [depth, setDepth] = useState(2);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const startResearch = useAriaStore((s) => s.startResearch);
  const status = useAriaStore((s) => s.status);

  const isLoading = status === 'searching' || status === 'running';

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;
    startResearch(query.trim(), maxPapers, depth);
  };

  const exampleQueries = [
    'How do large language models handle hallucination?',
    'What are the latest advances in CRISPR gene therapy?',
    'Transformer architectures for protein structure prediction',
    'Quantum error correction methods comparison',
  ];

  return (
    <div className="w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        {/* Main search input */}
        <div className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-aria-accent via-aria-purple to-aria-accent rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-500" />
          <div className="relative flex items-center bg-aria-surface border border-aria-border rounded-xl overflow-hidden">
            <span className="pl-4 text-aria-accent text-xl">🔬</span>
            <input
              id="search-input"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a research question..."
              className="flex-1 bg-transparent text-aria-text placeholder-aria-text-muted px-4 py-4 text-lg outline-none"
              disabled={isLoading}
            />
            <button
              id="search-submit"
              type="submit"
              disabled={!query.trim() || isLoading}
              className="btn-glow m-2 px-6 py-2.5 text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Researching...
                </span>
              ) : (
                'Research'
              )}
            </button>
          </div>
        </div>

        {/* Advanced options toggle */}
        <div className="mt-3 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-xs text-aria-text-dim hover:text-aria-accent transition-colors"
          >
            {showAdvanced ? '▾ Hide options' : '▸ Advanced options'}
          </button>
          <span className="text-xs text-aria-text-muted">
            arXiv · Semantic Scholar · PubMed
          </span>
        </div>

        {/* Advanced options panel */}
        {showAdvanced && (
          <div className="mt-2 p-4 glass-card flex gap-6 animate-slide-up">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-aria-text-dim">Max Papers</span>
              <input
                id="max-papers-input"
                type="number"
                min={5}
                max={100}
                value={maxPapers}
                onChange={(e) => setMaxPapers(Number(e.target.value))}
                className="w-20 bg-aria-bg border border-aria-border rounded px-2 py-1 text-sm text-aria-text outline-none focus:border-aria-accent"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs text-aria-text-dim">Citation Depth</span>
              <select
                id="depth-select"
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
                className="bg-aria-bg border border-aria-border rounded px-2 py-1 text-sm text-aria-text outline-none focus:border-aria-accent"
              >
                <option value={0}>0 — No citation trails</option>
                <option value={1}>1 — Direct references</option>
                <option value={2}>2 — Deep (recommended)</option>
                <option value={3}>3 — Exhaustive</option>
              </select>
            </label>
          </div>
        )}
      </form>

      {/* Example queries */}
      {status === 'idle' && (
        <div className="mt-6 animate-fade-in">
          <p className="text-xs text-aria-text-muted mb-2">Try an example:</p>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((eq, i) => (
              <button
                key={i}
                onClick={() => setQuery(eq)}
                className="text-xs px-3 py-1.5 rounded-full border border-aria-border text-aria-text-dim
                           hover:border-aria-accent/40 hover:text-aria-accent hover:bg-aria-accent/5
                           transition-all duration-200"
              >
                {eq.length > 45 ? eq.slice(0, 45) + '...' : eq}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
