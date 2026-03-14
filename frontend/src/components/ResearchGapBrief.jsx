import React from 'react';
import useAriaStore from '../store/useAriaStore';

export default function ResearchGapBrief() {
  const gaps = useAriaStore((s) => s.gaps);

  const gapsList = gaps?.gaps || [];

  if (!gaps || gapsList.length === 0) {
    return (
      <div className="glass-card p-8 text-center">
        <span className="text-4xl mb-3 block">🔍</span>
        <p className="text-aria-text-dim text-sm">Research gaps will appear here after analysis.</p>
      </div>
    );
  }

  const importanceColors = {
    high: 'border-aria-red/40 bg-aria-red/5',
    medium: 'border-aria-amber/40 bg-aria-amber/5',
    low: 'border-aria-text-muted/40 bg-aria-text-muted/5',
  };

  const importanceBadge = {
    high: 'bg-aria-red/20 text-aria-red',
    medium: 'bg-aria-amber/20 text-aria-amber',
    low: 'bg-aria-text-muted/20 text-aria-text-dim',
  };

  return (
    <div className="glass-card overflow-hidden animate-fade-in">
      <div className="px-4 py-3 border-b border-aria-border flex items-center gap-2">
        <span>🔍</span>
        <h3 className="text-sm font-semibold text-aria-text">Research Gap Brief</h3>
        <span className="ml-auto text-xs text-aria-text-muted">{gapsList.length} gaps identified</span>
      </div>
      <div className="p-4 space-y-3">
        {gapsList.map((gap, i) => {
          const importance = (gap.importance || 'medium').toLowerCase();
          return (
            <div
              key={i}
              className={`rounded-lg border p-4 transition-all duration-200 hover:shadow-lg ${importanceColors[importance] || importanceColors.medium}`}
            >
              <div className="flex items-start gap-3">
                <span className="text-lg font-bold text-aria-text-muted mt-0.5">
                  #{gap.rank || i + 1}
                </span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-sm font-semibold text-aria-text">{gap.gap}</h4>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${importanceBadge[importance] || importanceBadge.medium}`}>
                      {importance}
                    </span>
                  </div>
                  <p className="text-xs text-aria-text-dim leading-relaxed mt-1">
                    {gap.evidence}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
