import React from 'react';
import useAriaStore from '../store/useAriaStore';

const SessionHistory = () => {
  const sessionHistory = useAriaStore((s) => s.sessionHistory);
  const showHistory = useAriaStore((s) => s.showHistory);
  const restoreSession = useAriaStore((s) => s.restoreSession);
  const deleteSession = useAriaStore((s) => s.deleteSession);
  const clearHistory = useAriaStore((s) => s.clearHistory);
  const toggleHistory = useAriaStore((s) => s.toggleHistory);

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      const diffInMinutes = Math.floor((now - date) / (1000 * 60));
      return diffInMinutes < 1 ? 'Just now' : `${diffInMinutes}m ago`;
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      });
    }
  };

  const truncateText = (text, maxLength = 100) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (!showHistory) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-aria-card border border-aria-border rounded-xl max-w-4xl w-full max-h-[80vh] overflow-hidden shadow-2xl animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-aria-border">
          <div>
            <h2 className="text-xl font-bold text-aria-text">Session History</h2>
            <p className="text-sm text-aria-text-muted mt-1">
              {sessionHistory.length} {sessionHistory.length === 1 ? 'session' : 'sessions'} saved
            </p>
          </div>
          <div className="flex items-center gap-3">
            {sessionHistory.length > 0 && (
              <button
                onClick={clearHistory}
                className="text-xs text-aria-red hover:text-aria-red/80 transition-colors"
              >
                Clear All
              </button>
            )}
            <button
              onClick={toggleHistory}
              className="text-aria-text-muted hover:text-aria-text transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[60vh]">
          {sessionHistory.length === 0 ? (
            <div className="p-12 text-center">
              <div className="text-4xl mb-4">📚</div>
              <h3 className="text-lg font-semibold text-aria-text mb-2">No sessions yet</h3>
              <p className="text-sm text-aria-text-muted">
                Your research sessions will appear here after you complete your first search.
              </p>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {sessionHistory.map((session) => (
                <div
                  key={session.id}
                  className="bg-aria-surface/50 border border-aria-border rounded-lg p-4 hover:bg-aria-surface/70 transition-all cursor-pointer group"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div 
                      className="flex-1 min-w-0"
                      onClick={() => restoreSession(session)}
                    >
                      {/* Question */}
                      <h3 className="font-medium text-aria-text mb-2 group-hover:text-aria-accent transition-colors">
                        {truncateText(session.question, 150)}
                      </h3>
                      
                      {/* Metadata */}
                      <div className="flex items-center gap-4 text-xs text-aria-text-muted mb-2">
                        <span className="flex items-center gap-1">
                          📅 {formatDate(session.timestamp)}
                        </span>
                        <span className="flex items-center gap-1">
                          📄 {session.papers?.length || 0} papers
                        </span>
                        {session.status === 'completed' && (
                          <span className="flex items-center gap-1 text-aria-green">
                            ✓ Completed
                          </span>
                        )}
                      </div>
                      
                      {/* Summary preview */}
                      {session.summary && (
                        <p className="text-sm text-aria-text-dim line-clamp-2">
                          {truncateText(session.summary, 200)}
                        </p>
                      )}
                    </div>
                    
                    {/* Actions */}
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          restoreSession(session);
                        }}
                        className="px-3 py-1.5 text-xs bg-aria-accent/10 text-aria-accent rounded-md hover:bg-aria-accent/20 transition-colors"
                      >
                        Open
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.id);
                        }}
                        className="px-3 py-1.5 text-xs bg-aria-red/10 text-aria-red rounded-md hover:bg-aria-red/20 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SessionHistory;
