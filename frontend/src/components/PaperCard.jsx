import React, { useState } from 'react';
import useAriaStore from '../store/useAriaStore';

export default function PaperCard({ paper, index }) {
  const [expanded, setExpanded] = useState(false);
  const [explainLevel, setExplainLevel] = useState('undergrad');
  const [explanation, setExplanation] = useState('');
  const [explaining, setExplaining] = useState(false);
  
  // Get API base URL from store
  const API_BASE = import.meta.env.VITE_API_URL || '/api';

  const sourceColors = {
    arxiv: 'text-aria-amber border-aria-amber/30 bg-aria-amber/5',
    semantic_scholar: 'text-aria-accent border-aria-accent/30 bg-aria-accent/5',
    pubmed: 'text-aria-green border-aria-green/30 bg-aria-green/5',
  };
  const sourceLabel = { arxiv: 'arXiv', semantic_scholar: 'S2', pubmed: 'PubMed' };
  const badgeClass = sourceColors[paper.source] || 'text-aria-text-dim border-aria-border bg-aria-surface';

  const levels = [
    { id: 'child', label: '👶 Child', short: '👶' },
    { id: 'highschool', label: '🎒 High School', short: '🎒' },
    { id: 'undergrad', label: '🎓 Undergrad', short: '🎓' },
    { id: 'phd', label: '🔬 PhD', short: '🔬' },
  ];

  const handleExplain = async () => {
    if (!paper.abstract) return;
    setExplaining(true);
    try {
      const res = await fetch(`${API_BASE}/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: paper.abstract, level: explainLevel }),
      });
      const data = await res.json();
      setExplanation(data.explanation);
    } catch (e) {
      setExplanation('Failed to generate explanation. Please try again.');
    }
    setExplaining(false);
  };

  return (
    <div
      id={`paper-card-${index}`}
      className="glass-card p-4 hover:border-aria-accent/30 transition-all duration-300 cursor-pointer group"
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-aria-text group-hover:text-aria-accent transition-colors line-clamp-2">
            {paper.title || 'Untitled Paper'}
          </h3>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono ${badgeClass}`}>
              {sourceLabel[paper.source] || paper.source}
            </span>
            {paper.year && <span className="text-[10px] text-aria-text-muted">{paper.year}</span>}
            {paper.citation_count > 0 && (
              <span className="text-[10px] text-aria-text-muted">{paper.citation_count} citations</span>
            )}
            {paper.relevance_score != null && (
              <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono ${
                paper.relevance_score >= 0.5 ? 'text-aria-green border-aria-green/30 bg-aria-green/5' :
                paper.relevance_score >= 0.35 ? 'text-aria-amber border-aria-amber/30 bg-aria-amber/5' :
                'text-aria-red border-aria-red/30 bg-aria-red/5'
              }`}>
                {Math.round(paper.relevance_score * 100)}% match
              </span>
            )}
          </div>
        </div>
        <span className="text-aria-text-muted text-xs mt-1 flex-shrink-0">{expanded ? '▾' : '▸'}</span>
      </div>

      {/* Authors */}
      {paper.authors && paper.authors.length > 0 && (
        <p className="mt-2 text-xs text-aria-text-muted truncate">
          {paper.authors.slice(0, 3).join(', ')}
          {paper.authors.length > 3 ? ` +${paper.authors.length - 3} more` : ''}
        </p>
      )}

      {/* Expanded content */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-aria-border space-y-3 animate-slide-up" onClick={(e) => e.stopPropagation()}>
          {/* Abstract */}
          {paper.abstract && (
            <div>
              <h4 className="text-[10px] uppercase tracking-wider text-aria-text-muted mb-1">Abstract</h4>
              <p className="text-xs text-aria-text-dim leading-relaxed">
                {paper.abstract.length > 400 ? paper.abstract.slice(0, 400) + '...' : paper.abstract}
              </p>
            </div>
          )}

          {/* ✨ EXPLAIN LIKE I'M NEW — Feature 1 */}
          {paper.abstract && (
            <div className="bg-aria-surface/80 rounded-lg p-3 border border-aria-border/50">
              <h4 className="text-[10px] uppercase tracking-wider text-aria-accent mb-2 flex items-center gap-1">
                ✨ Explain Like I'm New
              </h4>
              <div className="flex items-center gap-1.5 mb-2">
                {levels.map((l) => (
                  <button
                    key={l.id}
                    onClick={() => { setExplainLevel(l.id); setExplanation(''); }}
                    className={`text-[10px] px-2 py-1 rounded-md border transition-all ${
                      explainLevel === l.id
                        ? 'bg-aria-accent/15 border-aria-accent/30 text-aria-accent'
                        : 'border-aria-border text-aria-text-muted hover:text-aria-text-dim'
                    }`}
                  >
                    {l.short} {l.id}
                  </button>
                ))}
                <button
                  onClick={handleExplain}
                  disabled={explaining}
                  className="ml-auto text-[10px] btn-glow px-3 py-1 rounded-md disabled:opacity-40"
                >
                  {explaining ? '⏳...' : '✨ Explain'}
                </button>
              </div>
              {explanation && (
                <div className="bg-aria-bg/50 rounded-md p-2.5 border border-aria-border/30">
                  <p className="text-xs text-aria-text leading-relaxed">{explanation}</p>
                </div>
              )}
            </div>
          )}

          {/* Core Claims */}
          {paper.core_claims && paper.core_claims.length > 0 && (
            <div>
              <h4 className="text-[10px] uppercase tracking-wider text-aria-text-muted mb-1">Core Claims</h4>
              <ul className="space-y-1">
                {paper.core_claims.map((claim, i) => (
                  <li key={i} className="text-xs text-aria-text-dim flex items-start gap-1.5">
                    <span className="text-aria-accent mt-0.5">•</span>
                    {claim}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Methodology */}
          {paper.methodology && (
            <div>
              <h4 className="text-[10px] uppercase tracking-wider text-aria-text-muted mb-1">Methodology</h4>
              <p className="text-xs text-aria-text-dim">{paper.methodology}</p>
            </div>
          )}

          {/* Keywords */}
          {paper.keywords && paper.keywords.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {paper.keywords.map((kw, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-aria-purple/10 text-aria-purple border border-aria-purple/20">
                  {kw}
                </span>
              ))}
            </div>
          )}

          {/* Link — multiple fallback strategies */}
          {(paper.url || paper.pdf_url || paper.doi || paper.arxiv_id) && (
            <a
              href={
                paper.url || 
                paper.pdf_url || 
                (paper.doi ? `https://doi.org/${paper.doi}` : null) ||
                (paper.arxiv_id ? `https://arxiv.org/abs/${paper.arxiv_id}` : null) ||
                '#'
              }
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-aria-accent hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              View paper ↗
            </a>
          )}
        </div>
      )}
    </div>
  );
}
