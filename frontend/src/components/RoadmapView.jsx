import React from 'react';
import useAriaStore from '../store/useAriaStore';

const STAGE_STYLES = [
  { color: 'border-slate-400', bg: 'bg-slate-400/5', label: '📖', gradient: 'from-slate-600 to-slate-400' },
  { color: 'border-aria-accent', bg: 'bg-aria-accent/5', label: '🔬', gradient: 'from-aria-accent to-blue-400' },
  { color: 'border-aria-purple', bg: 'bg-aria-purple/5', label: '🚀', gradient: 'from-aria-purple to-purple-400' },
  { color: 'border-aria-amber', bg: 'bg-aria-amber/5', label: '💡', gradient: 'from-aria-amber to-yellow-400' },
];

export default function RoadmapView() {
  const roadmap = useAriaStore((s) => s.roadmap);

  if (!roadmap || !roadmap.roadmap || roadmap.roadmap.length === 0) {
    return (
      <div className="glass-card p-8 text-center">
        <span className="text-3xl block mb-3">🗺️</span>
        <p className="text-sm text-aria-text-dim">
          No roadmap generated yet. Complete a research session to see your reading roadmap.
        </p>
      </div>
    );
  }

  const stages = roadmap.roadmap;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="glass-card p-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h2 className="text-lg font-bold text-aria-text flex items-center gap-2">
              🗺️ Research Roadmap
            </h2>
            <p className="text-xs text-aria-text-dim mt-1">
              A structured reading order from foundations to frontier
            </p>
          </div>
          <div className="flex items-center gap-4">
            {roadmap.estimated_reading_time && (
              <span className="text-xs font-mono text-aria-accent bg-aria-accent/10 px-3 py-1.5 rounded-lg border border-aria-accent/20">
                ⏱ {roadmap.estimated_reading_time}
              </span>
            )}
            {roadmap.suggested_first_paper && (
              <span className="text-xs text-aria-green bg-aria-green/10 px-3 py-1.5 rounded-lg border border-aria-green/20 max-w-xs truncate">
                ▶ Start: {roadmap.suggested_first_paper}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Connector line */}
        <div className="absolute left-6 top-8 bottom-8 w-0.5 bg-gradient-to-b from-slate-500 via-aria-accent via-aria-purple to-aria-amber opacity-30 hidden md:block" />

        <div className="space-y-4">
          {stages.map((stage, i) => {
            const style = STAGE_STYLES[i % STAGE_STYLES.length];
            return (
              <div key={i} className="relative md:pl-16">
                {/* Stage number dot */}
                <div className={`hidden md:flex absolute left-3 top-5 w-7 h-7 rounded-full ${style.bg} border-2 ${style.color} items-center justify-center text-xs font-bold text-aria-text`}>
                  {i + 1}
                </div>

                <div className={`glass-card p-5 border-l-2 ${style.color} hover:border-opacity-100 transition-all`}>
                  {/* Stage header */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{style.label}</span>
                    <h3 className="text-sm font-bold text-aria-text">{stage.stage}</h3>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border ${style.color} ${style.bg} font-mono`}>
                      Stage {i + 1}
                    </span>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-aria-text-dim mb-3">{stage.description}</p>

                  {/* Papers in this stage */}
                  {stage.papers && stage.papers.length > 0 && (
                    <div className="space-y-1.5 mb-3">
                      {stage.papers.map((title, j) => (
                        <div key={j} className={`flex items-start gap-2 ${style.bg} rounded-lg px-3 py-2 border border-aria-border/50`}>
                          <span className="text-aria-accent mt-0.5 flex-shrink-0">📄</span>
                          <span className="text-xs text-aria-text leading-relaxed">{title}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {stage.papers && stage.papers.length === 0 && stage.stage === 'Open Problems' && (
                    <div className="bg-aria-amber/5 border border-aria-amber/20 rounded-lg px-3 py-2 mb-3">
                      <span className="text-xs text-aria-amber">🎯 This is where YOUR research begins</span>
                    </div>
                  )}

                  {/* Why */}
                  {stage.why && (
                    <p className="text-[11px] text-aria-text-muted italic border-t border-aria-border/30 pt-2">
                      💡 {stage.why}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
