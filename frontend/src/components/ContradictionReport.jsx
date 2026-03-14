import React from 'react';
import ReactMarkdown from 'react-markdown';
import useAriaStore from '../store/useAriaStore';

export default function ContradictionReport() {
  const contradictions = useAriaStore((s) => s.contradictions);

  if (!contradictions) {
    return (
      <div className="glass-card p-8 text-center">
        <span className="text-4xl mb-3 block">⚠️</span>
        <p className="text-aria-text-dim text-sm">Contradiction report will appear here after analysis.</p>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden animate-fade-in">
      <div className="px-4 py-3 border-b border-aria-border flex items-center gap-2">
        <span>⚠️</span>
        <h3 className="text-sm font-semibold text-aria-text">Contradiction Report</h3>
      </div>
      <div className="p-5 markdown-content">
        <ReactMarkdown>{contradictions}</ReactMarkdown>
      </div>
    </div>
  );
}
