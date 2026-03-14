import React, { useEffect, useRef } from 'react';
import useAriaStore from '../store/useAriaStore';

const ICONS = {
  crawling: '🔍',
  filtering: '🎯',
  extracting: '🧠',
  scoring: '📊',
  graph_building: '🕸️',
  synthesizing: '✍️',
  roadmap: '🗺️',
  indexing: '📂',
  started: '🚀',
  completed: '🎉',
  error: '❌',
  default: '⚡',
};

export default function AgentStatusFeed() {
  const statusEvents = useAriaStore((s) => s.statusEvents);
  const progress = useAriaStore((s) => s.progress);
  const status = useAriaStore((s) => s.status);
  const feedRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [statusEvents]);

  if (status !== 'running' && statusEvents.length === 0) return null;

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-aria-border">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${status === 'running' ? 'bg-aria-green animate-pulse' : 'bg-aria-text-muted'}`} />
          <span className="text-sm font-medium text-aria-text">Agent Activity</span>
        </div>
        <span className="text-xs font-mono text-aria-text-dim">
          {progress > 0 && progress <= 100 ? `${progress}%` : '...'}
        </span>
      </div>

      {/* Progress bar */}
      {progress > 0 && (
        <div className="h-0.5 bg-aria-border">
          <div
            className="h-full bg-gradient-to-r from-aria-accent to-aria-purple transition-all duration-700 ease-out"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
      )}

      {/* Terminal feed */}
      <div
        ref={feedRef}
        className="max-h-64 overflow-y-auto px-4 py-3 font-mono text-xs space-y-1"
      >
        {statusEvents.map((evt, i) => (
          <div key={i} className="terminal-line flex items-start gap-2 py-0.5">
            <span className="flex-shrink-0 w-5 text-center">
              {ICONS[evt.event] || ICONS.default}
            </span>
            <span className="text-aria-text-dim opacity-50">
              {String(i).padStart(3, '0')}
            </span>
            <span className={`${evt.event === 'error' ? 'text-aria-red' : 'text-aria-text-dim'}`}>
              {evt.detail}
            </span>
          </div>
        ))}
        {status === 'running' && (
          <div className="terminal-line flex items-start gap-2 py-0.5">
            <span className="flex-shrink-0 w-5 text-center animate-pulse">▸</span>
            <span className="text-aria-accent cursor-blink">_</span>
          </div>
        )}
      </div>
    </div>
  );
}
