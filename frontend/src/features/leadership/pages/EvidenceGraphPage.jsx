// features/leadership/pages/EvidenceGraphPage.jsx
// Grafo de Evidencias: Decisión → Política → Objetivo → Proceso → KPI → Riesgo → Acción → Resultado

import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useI18n } from '../../../context/I18nContext';
import {
  getEvidenceGraph,
  createEvidenceNode,
  approveEvidenceNode,
  createEvidenceEdge,
  deleteEvidenceNode,
} from '../api/leadershipApi';
import { showConfirm } from '../../../services/dialogs';

const NODE_TYPE_COLORS = {
  directive_decision: { bg: 'bg-red-100 dark:bg-red-900/40', text: 'text-red-700 dark:text-red-300', border: 'border-red-300 dark:border-red-700', icon: '🎯' },
  quality_policy: { bg: 'bg-blue-100 dark:bg-blue-900/40', text: 'text-blue-700 dark:text-blue-300', border: 'border-blue-300 dark:border-blue-700', icon: '📋' },
  objective: { bg: 'bg-purple-100 dark:bg-purple-900/40', text: 'text-purple-700 dark:text-purple-300', border: 'border-purple-300 dark:border-purple-700', icon: '🎯' },
  process: { bg: 'bg-cyan-100 dark:bg-cyan-900/40', text: 'text-cyan-700 dark:text-cyan-300', border: 'border-cyan-300 dark:border-cyan-700', icon: '⚙️' },
  kpi: { bg: 'bg-green-100 dark:bg-green-900/40', text: 'text-green-700 dark:text-green-300', border: 'border-green-300 dark:border-green-700', icon: '📊' },
  risk: { bg: 'bg-orange-100 dark:bg-orange-900/40', text: 'text-orange-700 dark:text-orange-300', border: 'border-orange-300 dark:border-orange-700', icon: '⚠️' },
  action: { bg: 'bg-yellow-100 dark:bg-yellow-900/40', text: 'text-yellow-700 dark:text-yellow-300', border: 'border-yellow-300 dark:border-yellow-700', icon: '▶️' },
  result: { bg: 'bg-emerald-100 dark:bg-emerald-900/40', text: 'text-emerald-700 dark:text-emerald-300', border: 'border-emerald-300 dark:border-emerald-700', icon: '✅' },
};

const NODE_TYPES = Object.keys(NODE_TYPE_COLORS);
const EDGE_TYPES = ['derives_from', 'supports', 'measures', 'mitigates', 'generates', 'implements'];

const nodeFormInit = { node_type: 'directive_decision', title: '', description: '', data_source: '', expected_impact: '' };
const edgeFormInit = { source: '', target: '', edge_type: 'supports', label: '' };

const EvidenceGraphPage = () => {
  const { t } = useI18n();
  const { currentOrganization } = useAuth();
  const orgId = currentOrganization?.id || null;

  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showNodeForm, setShowNodeForm] = useState(false);
  const [showEdgeForm, setShowEdgeForm] = useState(false);
  const [nodeForm, setNodeForm] = useState(nodeFormInit);
  const [edgeForm, setEdgeForm] = useState(edgeFormInit);
  const [filterType, setFilterType] = useState('all');

  const loadGraph = useCallback(async () => {
    if (!orgId) { setLoading(false); return; }
    try {
      setLoading(true);
      const data = await getEvidenceGraph(orgId);
      setNodes(data.nodes || []);
      setEdges(data.edges || []);
    } catch {
      setError(t('modules.leadership.evidenceGraph.messages.loadError'));
    } finally {
      setLoading(false);
    }
  }, [orgId, t]);

  useEffect(() => { loadGraph(); }, [loadGraph]);

  const handleCreateNode = async (e) => {
    e.preventDefault();
    if (!orgId) return;
    try {
      await createEvidenceNode({ ...nodeForm, organization_id: orgId });
      setShowNodeForm(false);
      setNodeForm(nodeFormInit);
      await loadGraph();
    } catch { setError(t('modules.leadership.evidenceGraph.messages.saveError')); }
  };

  const handleApproveNode = async (nodeId) => {
    try {
      await approveEvidenceNode(nodeId);
      await loadGraph();
    } catch (err) {
      setError(err?.response?.data?.error || t('modules.leadership.evidenceGraph.messages.approveError'));
    }
  };

  const handleDeleteNode = async (nodeId) => {
    if (!await showConfirm(t('modules.leadership.evidenceGraph.messages.confirmDelete'))) return;
    try {
      await deleteEvidenceNode(nodeId);
      if (selected?.id === nodeId) setSelected(null);
      await loadGraph();
    } catch { setError(t('modules.leadership.evidenceGraph.messages.deleteError')); }
  };

  const handleCreateEdge = async (e) => {
    e.preventDefault();
    try {
      await createEvidenceEdge(edgeForm);
      setShowEdgeForm(false);
      setEdgeForm(edgeFormInit);
      await loadGraph();
    } catch { setError(t('modules.leadership.evidenceGraph.messages.edgeSaveError')); }
  };

  const filteredNodes = filterType === 'all' ? nodes : nodes.filter(n => n.node_type === filterType);

  const getNodeConnections = (nodeId) => ({
    outgoing: edges.filter(e => e.source === nodeId),
    incoming: edges.filter(e => e.target === nodeId),
  });

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
    </div>
  );

  return (
    <div className="p-6 bg-slate-50 dark:bg-slate-900 min-h-screen space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            {t('modules.leadership.evidenceGraph.title')}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t('modules.leadership.evidenceGraph.subtitle')}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setShowEdgeForm(true)} className="px-3 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm hover:bg-slate-300">
            🔗 {t('modules.leadership.evidenceGraph.buttons.newEdge')}
          </button>
          <button onClick={() => setShowNodeForm(true)} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
            + {t('modules.leadership.evidenceGraph.buttons.newNode')}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-red-700 dark:text-red-300 text-sm">
          {error} <button onClick={() => setError('')} className="ml-2">✕</button>
        </div>
      )}

      {/* Leyenda del grafo */}
      <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-3">
          {t('modules.leadership.evidenceGraph.chain')}
        </p>
        <div className="flex flex-wrap gap-2">
          {NODE_TYPES.map(type => {
            const style = NODE_TYPE_COLORS[type];
            const count = nodes.filter(n => n.node_type === type).length;
            return (
              <button
                key={type}
                onClick={() => setFilterType(filterType === type ? 'all' : type)}
                className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border transition-all ${style.bg} ${style.text} ${style.border} ${filterType === type ? 'ring-2 ring-offset-1 ring-blue-500' : ''}`}
              >
                {style.icon} {type.replace(/_/g, ' ')} ({count})
              </button>
            );
          })}
        </div>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 text-center">
          <p className="text-2xl font-bold text-slate-900 dark:text-white">{nodes.length}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t('modules.leadership.evidenceGraph.stats.nodes')}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 text-center">
          <p className="text-2xl font-bold text-slate-900 dark:text-white">{edges.length}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t('modules.leadership.evidenceGraph.stats.edges')}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 text-center">
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
            {nodes.filter(n => n.approved_at).length}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t('modules.leadership.evidenceGraph.stats.approved')}</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 text-center">
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
            {nodes.filter(n => !n.approved_at).length}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{t('modules.leadership.evidenceGraph.stats.pending')}</p>
        </div>
      </div>

      {/* Nodos grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredNodes.length === 0 ? (
          <div className="col-span-full text-center py-12 text-slate-500 dark:text-slate-400">
            <p className="text-3xl mb-3">🕸️</p>
            <p className="text-sm">{t('modules.leadership.evidenceGraph.messages.empty')}</p>
          </div>
        ) : (
          filteredNodes.map(node => {
            const style = NODE_TYPE_COLORS[node.node_type] || NODE_TYPE_COLORS.result;
            const { outgoing, incoming } = getNodeConnections(node.id);
            return (
              <div
                key={node.id}
                onClick={() => setSelected(selected?.id === node.id ? null : node)}
                className={`cursor-pointer bg-white dark:bg-slate-800 rounded-lg border p-4 transition-all hover:shadow-md ${
                  selected?.id === node.id
                    ? `${style.border} ring-1 ring-offset-0`
                    : 'border-slate-200 dark:border-slate-700'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${style.bg} shrink-0`}>
                    {style.icon}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${style.bg} ${style.text}`}>
                        {node.node_type_display || node.node_type}
                      </span>
                      {node.approved_at ? (
                        <span className="text-xs text-green-500">✓</span>
                      ) : (
                        <span className="text-xs text-amber-500">⏳</span>
                      )}
                    </div>
                    <p className="font-medium text-sm text-slate-900 dark:text-white mt-1 truncate">{node.title}</p>
                    {node.description && (
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{node.description}</p>
                    )}
                    <div className="flex gap-3 mt-2 text-xs text-slate-400">
                      <span>↗ {outgoing.length}</span>
                      <span>↙ {incoming.length}</span>
                      {node.responsible_name && <span>👤 {node.responsible_name}</span>}
                    </div>
                  </div>
                </div>

                {/* Acciones */}
                <div className="flex gap-2 mt-3 justify-end">
                  {!node.approved_at && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleApproveNode(node.id); }}
                      className="text-xs px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      ✓ Aprobar
                    </button>
                  )}
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteNode(node.id); }}
                    className="text-xs text-red-500 hover:text-red-700"
                  >
                    ✕
                  </button>
                </div>

                {/* Conexiones */}
                {selected?.id === node.id && (outgoing.length > 0 || incoming.length > 0) && (
                  <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700 text-xs space-y-1">
                    {outgoing.map(e => {
                      const targetNode = nodes.find(n => n.id === e.target);
                      return (
                        <p key={e.id} className="text-slate-500 dark:text-slate-400">
                          → [{e.edge_type_display || e.edge_type}] {targetNode?.title || e.target_title}
                        </p>
                      );
                    })}
                    {incoming.map(e => {
                      const sourceNode = nodes.find(n => n.id === e.source);
                      return (
                        <p key={e.id} className="text-slate-400 dark:text-slate-500">
                          ← [{e.edge_type_display || e.edge_type}] {sourceNode?.title || e.source_title}
                        </p>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Modal: Nuevo Nodo */}
      {showNodeForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-lg">
            <div className="p-6">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                {t('modules.leadership.evidenceGraph.form.newNodeTitle')}
              </h2>
              <form onSubmit={handleCreateNode} className="space-y-4">
                <select
                  value={nodeForm.node_type}
                  onChange={e => setNodeForm(f => ({ ...f, node_type: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                >
                  {NODE_TYPES.map(t => <option key={t} value={t}>{NODE_TYPE_COLORS[t].icon} {t.replace(/_/g, ' ')}</option>)}
                </select>
                <input
                  type="text"
                  placeholder={t('modules.leadership.evidenceGraph.form.title')}
                  value={nodeForm.title}
                  onChange={e => setNodeForm(f => ({ ...f, title: e.target.value }))}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                />
                <textarea
                  placeholder={t('modules.leadership.evidenceGraph.form.description')}
                  value={nodeForm.description}
                  onChange={e => setNodeForm(f => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                />
                <input
                  type="text"
                  placeholder={t('modules.leadership.evidenceGraph.form.dataSource')}
                  value={nodeForm.data_source}
                  onChange={e => setNodeForm(f => ({ ...f, data_source: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                />
                <textarea
                  placeholder={t('modules.leadership.evidenceGraph.form.expectedImpact')}
                  value={nodeForm.expected_impact}
                  onChange={e => setNodeForm(f => ({ ...f, expected_impact: e.target.value }))}
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                />
                <div className="flex gap-3">
                  <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                    {t('common.buttons.save')}
                  </button>
                  <button type="button" onClick={() => setShowNodeForm(false)} className="flex-1 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm">
                    {t('common.buttons.cancel')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Nueva Arista */}
      {showEdgeForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md">
            <div className="p-6">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                {t('modules.leadership.evidenceGraph.form.newEdgeTitle')}
              </h2>
              <form onSubmit={handleCreateEdge} className="space-y-4">
                <select
                  value={edgeForm.source}
                  onChange={e => setEdgeForm(f => ({ ...f, source: e.target.value }))}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                >
                  <option value="">{t('modules.leadership.evidenceGraph.form.sourceNode')}</option>
                  {nodes.map(n => <option key={n.id} value={n.id}>{NODE_TYPE_COLORS[n.node_type]?.icon} {n.title}</option>)}
                </select>
                <select
                  value={edgeForm.edge_type}
                  onChange={e => setEdgeForm(f => ({ ...f, edge_type: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                >
                  {EDGE_TYPES.map(et => <option key={et} value={et}>{et.replace(/_/g, ' ')}</option>)}
                </select>
                <select
                  value={edgeForm.target}
                  onChange={e => setEdgeForm(f => ({ ...f, target: e.target.value }))}
                  required
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                >
                  <option value="">{t('modules.leadership.evidenceGraph.form.targetNode')}</option>
                  {nodes.map(n => <option key={n.id} value={n.id}>{NODE_TYPE_COLORS[n.node_type]?.icon} {n.title}</option>)}
                </select>
                <input
                  type="text"
                  placeholder={t('modules.leadership.evidenceGraph.form.edgeLabel')}
                  value={edgeForm.label}
                  onChange={e => setEdgeForm(f => ({ ...f, label: e.target.value }))}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-sm"
                />
                <div className="flex gap-3">
                  <button type="submit" className="flex-1 py-2 bg-blue-600 text-white rounded-lg text-sm">
                    {t('common.buttons.save')}
                  </button>
                  <button type="button" onClick={() => setShowEdgeForm(false)} className="flex-1 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm">
                    {t('common.buttons.cancel')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvidenceGraphPage;
