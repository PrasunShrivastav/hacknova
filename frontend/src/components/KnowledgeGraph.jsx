import React, { useCallback, useRef, useEffect, useState } from 'react';
import useAriaStore from '../store/useAriaStore';

export default function KnowledgeGraph() {
  const graphData = useAriaStore((s) => s.graphData);
  const canvasRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [ForceGraph, setForceGraph] = useState(null);

  // Dynamically import react-force-graph-2d
  useEffect(() => {
    import('react-force-graph-2d').then((mod) => {
      setForceGraph(() => mod.default);
    }).catch(() => {
      console.warn('react-force-graph-2d not available');
    });
  }, []);

  if (!graphData || (!graphData.nodes?.length)) {
    return (
      <div className="glass-card p-8 text-center">
        <span className="text-4xl mb-3 block">🕸️</span>
        <p className="text-aria-text-dim text-sm">Knowledge graph will appear here once research is complete.</p>
      </div>
    );
  }

  const edgeColors = {
    supports: '#10b981',
    contradicts: '#ef4444',
    cites: '#475569',
    related: '#64748b',
  };

  const domainColors = [
    '#00d4ff', '#7c3aed', '#f59e0b', '#10b981', '#ef4444',
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#8b5cf6',
  ];

  // Assign colors by domain
  const domains = [...new Set(graphData.nodes.map((n) => n.domain || 'unknown'))];
  const domainColorMap = {};
  domains.forEach((d, i) => {
    domainColorMap[d] = domainColors[i % domainColors.length];
  });

  const formattedData = {
    nodes: graphData.nodes.map((n) => ({
      ...n,
      color: domainColorMap[n.domain || 'unknown'],
      val: Math.max(2, Math.min(8, (n.citation_count || 0) / 100 + 2)),
    })),
    links: graphData.edges.map((e) => ({
      source: e.source,
      target: e.target,
      color: edgeColors[e.edge_type] || '#475569',
      edgeType: e.edge_type,
      reason: e.reason,
    })),
  };

  const handleNodeClick = useCallback((node) => {
    setSelectedNode(node);
  }, []);

  return (
    <div className="glass-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-aria-border">
        <h3 className="text-sm font-semibold text-aria-text">Knowledge Graph</h3>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-[10px] text-aria-text-muted">
            <span className="w-2 h-2 rounded-full bg-aria-green" /> supports
          </span>
          <span className="flex items-center gap-1 text-[10px] text-aria-text-muted">
            <span className="w-2 h-2 rounded-full bg-aria-red" /> contradicts
          </span>
          <span className="flex items-center gap-1 text-[10px] text-aria-text-muted">
            <span className="w-2 h-2 rounded-full bg-aria-text-muted" /> cites
          </span>
        </div>
      </div>

      {/* Graph */}
      <div className="relative" style={{ height: '450px' }}>
        {ForceGraph ? (
          <ForceGraph
            ref={canvasRef}
            graphData={formattedData}
            nodeLabel={(node) => node.title || node.label}
            nodeColor={(node) => node.color}
            nodeRelSize={5}
            linkColor={(link) => link.color}
            linkWidth={(link) => (link.edgeType === 'contradicts' ? 2 : 1)}
            linkDirectionalArrowLength={3}
            linkDirectionalArrowRelPos={1}
            onNodeClick={handleNodeClick}
            backgroundColor="#050810"
            width={undefined}
            height={450}
            cooldownTicks={100}
            nodeCanvasObjectMode={() => 'after'}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const fontSize = Math.max(8, 12 / globalScale);
              ctx.font = `${fontSize}px Inter, sans-serif`;
              ctx.fillStyle = 'rgba(226, 232, 240, 0.7)';
              ctx.textAlign = 'center';
              ctx.fillText(
                (node.label || '').slice(0, 20),
                node.x,
                node.y + (node.val || 4) + fontSize
              );
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-aria-text-dim text-sm">
            Loading graph visualization...
          </div>
        )}
      </div>

      {/* Selected node detail */}
      {selectedNode && (
        <div className="border-t border-aria-border px-4 py-3 animate-slide-up">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-aria-text">{selectedNode.title}</h4>
              <p className="text-xs text-aria-text-muted mt-1">
                {selectedNode.year && `${selectedNode.year} · `}
                {selectedNode.domain || 'Unknown domain'}
                {selectedNode.citation_count > 0 && ` · ${selectedNode.citation_count} citations`}
              </p>
              {selectedNode.claims && selectedNode.claims.length > 0 && (
                <div className="mt-2">
                  <p className="text-[10px] uppercase tracking-wider text-aria-text-muted mb-1">Claims</p>
                  {selectedNode.claims.slice(0, 2).map((c, i) => (
                    <p key={i} className="text-xs text-aria-text-dim">• {c}</p>
                  ))}
                </div>
              )}
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-aria-text-muted hover:text-aria-text text-xs ml-2"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Stats bar - fixed positioning */}
      <div className="sticky bottom-0 flex items-center justify-between gap-4 px-4 py-3 border-t border-aria-border bg-aria-bg/95 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <span className="text-[10px] text-aria-text-muted">{graphData.nodes.length} nodes</span>
          <span className="text-[10px] text-aria-text-muted">{graphData.edges.length} edges</span>
          <span className="text-[10px] text-aria-text-muted">{domains.length} domains</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1 text-[10px] text-aria-text-muted">
            <span className="w-2 h-2 rounded-full bg-aria-green" /> supports
          </span>
          <span className="flex items-center gap-1 text-[10px] text-aria-text-muted">
            <span className="w-2 h-2 rounded-full bg-aria-red" /> contradicts
          </span>
          <span className="flex items-center gap-1 text-[10px] text-aria-text-muted">
            <span className="w-2 h-2 rounded-full bg-aria-text-muted" /> cites
          </span>
        </div>
      </div>
    </div>
  );
}
