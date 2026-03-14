import React, { useState } from 'react';

export default function PaperCard({ paper, index }) {
  const [expanded, setExpanded] = useState(false);

  const sourceColors = {
    arxiv: 'text-aria-amber border-aria-amber/30 bg-aria-amber/5',
    semantic_scholar: 'text-aria-accent border-aria-accent/30 bg-aria-accent/5',
    pubmed: 'text-aria-green border-aria-green/30 bg-aria-green/5',
  };

  const sourceLabel = {
    arxiv: 'arXiv',
    semantic_scholar: 'S2',
    pubmed: 'PubMed',
  };

  const badgeClass = sourceColors[paper.source] || 'text-aria-text-dim border-aria-border bg-aria-surface';

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
            {paper.year && (
              <span className="text-[10px] text-aria-text-muted">{paper.year}</span>
            )}
            {paper.citation_count > 0 && (
              <span className="text-[10px] text-aria-text-muted">
                {paper.citation_count} citations
              </span>
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
        <span className="text-aria-text-muted text-xs mt-1 flex-shrink-0">
          {expanded ? '▾' : '▸'}
        </span>
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
        <div className="mt-3 pt-3 border-t border-aria-border space-y-3 animate-slide-up">
          {/* Abstract */}
          {paper.abstract && (
            <div>
              <h4 className="text-[10px] uppercase tracking-wider text-aria-text-muted mb-1">Abstract</h4>
              <p className="text-xs text-aria-text-dim leading-relaxed">
                {paper.abstract.length > 400 ? paper.abstract.slice(0, 400) + '...' : paper.abstract}
              </p>
            </div>
          )}

          {/* Claims */}
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

          {/* Link */}
          {paper.url && (
            <a
              href={paper.url}
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
