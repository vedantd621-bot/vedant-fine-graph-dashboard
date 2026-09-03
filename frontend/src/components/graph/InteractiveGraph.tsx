import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { GraphEdge, GraphNode, GraphPayload } from '../../types';
import { ZoomIn, ZoomOut, Maximize2, ShieldAlert } from 'lucide-react';

interface InteractiveGraphProps {
  data: GraphPayload;
  focalAccountId?: string;
  onSelectNode?: (nodeId: string) => void;
  height?: number;
}

export const InteractiveGraph: React.FC<InteractiveGraphProps> = ({
  data,
  focalAccountId,
  onSelectNode,
  height = 500,
}) => {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<GraphEdge | null>(null);

  const getNodeColor = (node: GraphNode): string => {
    if (node.type === 'Bank') return '#a855f7'; // Purple
    if (node.type === 'Person') return '#38bdf8'; // Sky blue
    if (node.is_frozen) return '#64748b'; // Frozen gray

    switch (node.risk_level) {
      case 'CRITICAL':
        return '#f43f5e'; // Rose
      case 'HIGH':
        return '#f59e0b'; // Amber
      case 'MEDIUM':
        return '#6366f1'; // Indigo
      case 'LOW':
      default:
        return '#10b981'; // Emerald
    }
  };

  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return;

    const width = svgRef.current.clientWidth || 800;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous render

    // Define Arrow Marker for directed transfers
    const defs = svg.append('defs');
    defs
      .append('marker')
      .attr('id', 'arrow-transfer')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#94a3b8');

    defs
      .append('marker')
      .attr('id', 'arrow-owns')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 5)
      .attr('markerHeight', 5)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#38bdf8');

    // Container for zoom/pan
    const container = svg.append('g').attr('class', 'graph-container');

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Deep clone data to avoid simulation mutation issues
    const nodes: GraphNode[] = data.nodes.map((d) => ({ ...d }));
    const edges: GraphEdge[] = data.edges.map((d) => ({ ...d }));

    // Force Simulation
    const simulation = d3
      .forceSimulation<GraphNode>(nodes)
      .force(
        'link',
        d3
          .forceLink<GraphNode, GraphEdge>(edges)
          .id((d) => d.id)
          .distance(120)
      )
      .force('charge', d3.forceManyBody().strength(-350))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(35));

    // Render Edges
    const link = container
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(edges)
      .enter()
      .append('line')
      .attr('stroke', (d) => {
        if (d.type === 'OWNS') return '#38bdf8';
        if (d.type === 'HOSTED_BY') return '#a855f7';
        return '#64748b';
      })
      .attr('stroke-width', (d) => (d.amount && d.amount > 20000 ? 2.5 : 1.5))
      .attr('stroke-dasharray', (d) => (d.type === 'OWNS' ? '4 3' : 'none'))
      .attr('marker-end', (d) => (d.type === 'OWNS' ? 'url(#arrow-owns)' : 'url(#arrow-transfer)'))
      .on('mouseenter', (event, d) => setHoveredEdge(d))
      .on('mouseleave', () => setHoveredEdge(null));

    // Render Edge Labels for amounts
    const edgeLabel = container
      .append('g')
      .attr('class', 'edge-labels')
      .selectAll('text')
      .data(edges.filter((e) => e.amount !== undefined))
      .enter()
      .append('text')
      .attr('font-size', '9px')
      .attr('fill', '#cbd5e1')
      .attr('text-anchor', 'middle')
      .attr('dy', -3)
      .text((d) => (d.amount ? `$${(d.amount / 1000).toFixed(1)}k` : ''));

    // Drag handlers
    const drag = d3
      .drag<SVGGElement, GraphNode>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    // Render Nodes Group
    const nodeGroup = container
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .call(drag as any)
      .on('click', (event, d) => {
        if (onSelectNode && d.type === 'Account') {
          onSelectNode(d.id);
        }
      })
      .on('mouseenter', (event, d) => setHoveredNode(d))
      .on('mouseleave', () => setHoveredNode(null));

    // Node Circle
    nodeGroup
      .append('circle')
      .attr('r', (d) => (d.id === focalAccountId ? 20 : d.type === 'Account' ? 15 : 12))
      .attr('fill', (d) => getNodeColor(d))
      .attr('stroke', (d) => (d.id === focalAccountId ? '#38bdf8' : '#0f172a'))
      .attr('stroke-width', (d) => (d.id === focalAccountId ? 3 : 2))
      .attr('cursor', 'pointer');

    // Node Labels
    nodeGroup
      .append('text')
      .attr('dy', (d) => (d.type === 'Account' ? 26 : 22))
      .attr('text-anchor', 'middle')
      .attr('fill', '#f1f5f9')
      .attr('font-size', '10px')
      .attr('font-weight', (d) => (d.id === focalAccountId ? 'bold' : 'normal'))
      .text((d) => d.id);

    // Simulation Tick Update
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      edgeLabel
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2);

      nodeGroup.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [data, focalAccountId, height, onSelectNode]);

  return (
    <div className="relative rounded-xl bg-slate-950 border border-slate-800 overflow-hidden">
      {/* Graph Toolbar */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-2 bg-slate-900/80 backdrop-blur p-1.5 rounded-lg border border-slate-800 text-slate-300">
        <span className="text-[11px] font-medium text-slate-400 px-2">
          {data.nodes.length} nodes · {data.edges.length} edges
        </span>
      </div>

      {/* Interactive SVG Canvas */}
      <svg ref={svgRef} width="100%" height={height} className="cursor-grab active:cursor-grabbing" />

      {/* Floating Tooltip for Hovered Node */}
      {hoveredNode && (
        <div className="absolute bottom-4 left-4 z-20 p-3 rounded-lg bg-slate-900/95 border border-slate-700 shadow-xl text-xs space-y-1 backdrop-blur max-w-xs">
          <div className="flex items-center justify-between gap-3">
            <span className="font-bold text-slate-100">{hoveredNode.label}</span>
            <span
              className="text-[10px] font-bold px-1.5 py-0.5 rounded"
              style={{ backgroundColor: `${getNodeColor(hoveredNode)}33`, color: getNodeColor(hoveredNode) }}
            >
              {hoveredNode.risk_level || hoveredNode.type}
            </span>
          </div>
          {hoveredNode.risk_score !== undefined && (
            <div className="text-slate-300">
              Risk Score: <span className="font-bold text-slate-100">{hoveredNode.risk_score.toFixed(1)}/100</span>
            </div>
          )}
          {hoveredNode.metadata && (
            <div className="text-slate-400 text-[11px]">
              {hoveredNode.metadata.owner_name && <div>Owner: {hoveredNode.metadata.owner_name}</div>}
              {hoveredNode.metadata.bank_name && <div>Bank: {hoveredNode.metadata.bank_name}</div>}
            </div>
          )}
        </div>
      )}

      {/* Floating Tooltip for Hovered Edge */}
      {hoveredEdge && (
        <div className="absolute bottom-4 right-4 z-20 p-2.5 rounded-lg bg-slate-900/95 border border-slate-700 shadow-xl text-xs space-y-1 backdrop-blur">
          <div className="font-bold text-slate-200">
            {hoveredEdge.type}: {typeof hoveredEdge.source === 'object' ? hoveredEdge.source.id : hoveredEdge.source} → {typeof hoveredEdge.target === 'object' ? hoveredEdge.target.id : hoveredEdge.target}
          </div>
          {hoveredEdge.amount !== undefined && (
            <div className="text-cyan-400 font-semibold">
              Amount: ${hoveredEdge.amount.toLocaleString()} {hoveredEdge.currency}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
