import React from 'react';
import useAriaStore from '../store/useAriaStore';
import AgentStatusFeed from '../components/AgentStatusFeed';
import LiteratureSummary from '../components/LiteratureSummary';
import ContradictionReport from '../components/ContradictionReport';
import ResearchGapBrief from '../components/ResearchGapBrief';
import KnowledgeGraph from '../components/KnowledgeGraph';
import RoadmapView from '../components/RoadmapView';
import PaperCard from '../components/PaperCard';
import ChatInterface from '../components/ChatInterface';

const TABS = [
  { id: 'summary', label: 'Summary', icon: '📄' },
  { id: 'roadmap', label: 'Roadmap', icon: '🗺️' },
  { id: 'contradictions', label: 'Contradictions', icon: '⚠️' },
  { id: 'gaps', label: 'Research Gaps', icon: '🔍' },
  { id: 'graph', label: 'Knowledge Graph', icon: '🕸️' },
  { id: 'papers', label: 'Papers', icon: '📚' },
];

export default function ResultsPage() {
  const status = useAriaStore((s) => s.status);
  const question = useAriaStore((s) => s.question);
  const papers = useAriaStore((s) => s.papers);
  const activeTab = useAriaStore((s) => s.activeTab);
  const setActiveTab = useAriaStore((s) => s.setActiveTab);
  const reset = useAriaStore((s) => s.reset);
  const progress = useAriaStore((s) => s.progress);
  const error = useAriaStore((s) => s.error);

  const isRunning = status === 'running';

  return (
    <div className="min-h-screen pb-24">
      {/* Top bar */}
      <header className="sticky top-0 z-40 bg-aria-bg/80 backdrop-blur-md border-b border-aria-border">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              id="back-home"
              onClick={reset}
              className="text-aria-text-muted hover:text-aria-accent transition-colors"
            >
              ← New Search
            </button>
            <div className="h-5 w-px bg-aria-border" />
            <h1 className="text-sm font-semibold text-aria-text truncate max-w-lg">
              <span className="gradient-text font-bold mr-1.5">ARIA</span>
              {question && <span className="text-aria-text-dim font-normal">— {question}</span>}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            {isRunning && (
              <span className="flex items-center gap-2 text-xs text-aria-accent">
                <span className="w-2 h-2 rounded-full bg-aria-green animate-pulse" />
                Analyzing... {progress}%
              </span>
            )}
            {status === 'completed' && (
              <span className="text-xs text-aria-green">
                ✓ {papers.length} papers analyzed
              </span>
            )}
          </div>
        </div>

        {/* Progress bar */}
        {isRunning && (
          <div className="h-0.5 bg-aria-border">
            <div
              className="h-full bg-gradient-to-r from-aria-accent to-aria-purple transition-all duration-700"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </header>

      {/* Status feed */}
      {isRunning && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <AgentStatusFeed />
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <div className="glass-card border-aria-red/30 p-4">
            <p className="text-sm text-aria-red">❌ {error}</p>
          </div>
        </div>
      )}

      {/* Tab navigation */}
      {(status === 'completed' || papers.length > 0) && (
        <div className="max-w-7xl mx-auto px-4 mt-6">
          <div className="flex items-center gap-1 bg-aria-surface/50 p-1 rounded-lg border border-aria-border w-fit overflow-x-auto">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                id={`tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all whitespace-nowrap
                  ${activeTab === tab.id
                    ? 'bg-aria-card text-aria-text border border-aria-border shadow-sm'
                    : 'text-aria-text-muted hover:text-aria-text-dim'
                  }`}
              >
                <span>{tab.icon}</span>
                {tab.label}
                {tab.id === 'papers' && papers.length > 0 && (
                  <span className="text-[10px] bg-aria-accent/10 text-aria-accent px-1.5 rounded-full">
                    {papers.length}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tab content */}
      {(status === 'completed' || papers.length > 0) && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          {activeTab === 'summary' && <LiteratureSummary />}
          {activeTab === 'roadmap' && <RoadmapView />}
          {activeTab === 'contradictions' && <ContradictionReport />}
          {activeTab === 'gaps' && <ResearchGapBrief />}
          {activeTab === 'graph' && <KnowledgeGraph />}
          {activeTab === 'papers' && (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {papers.map((paper, i) => (
                <PaperCard key={i} paper={paper} index={i} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Chat interface (floating) */}
      <ChatInterface />
    </div>
  );
}
