import { useQuery } from '@tanstack/react-query';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { workflowApi, executionApi } from '../services/api';
import { ArrowLeft, Edit3, Play, BarChart3 } from 'lucide-react';

export function WorkflowDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: workflow } = useQuery({
    queryKey: ['workflow', id],
    queryFn: () => workflowApi.get(id!),
  });

  const { data: stats } = useQuery({
    queryKey: ['execution-stats', id],
    queryFn: () => executionApi.stats(id!),
  });

  const { data: recentExecs } = useQuery({
    queryKey: ['recent-executions', id],
    queryFn: () => executionApi.search({ workflow_id: id, limit: 10 }),
  });

  if (!workflow) return <div className="animate-pulse h-96 bg-surface-100 rounded-xl" />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/workflows" className="p-2 rounded-lg hover:bg-surface-100">
          <ArrowLeft className="w-5 h-5 text-surface-500" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{workflow.name}</h1>
            <span className={`badge-${workflow.publication_status === 'published' ? 'success' : workflow.publication_status === 'archived' ? 'neutral' : 'info'}`}>
              {workflow.publication_status}
            </span>
            <span className="badge-neutral">v{workflow.version}</span>
          </div>
          {workflow.description && (
            <p className="text-surface-500 mt-1">{workflow.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <button onClick={() => navigate(`/workflows/${id}/builder`)} className="btn-primary">
            <Edit3 className="w-4 h-4" /> Open Builder
          </button>
          <button onClick={() => workflowApi.trigger('manual', { workflow_id: id })} className="btn-secondary">
            <Play className="w-4 h-4" /> Trigger
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="stat-card"><p className="stat-label">Total</p><p className="stat-value">{stats.total}</p></div>
          <div className="stat-card"><p className="stat-label">Success Rate</p><p className="stat-value text-emerald-600">{stats.success_rate}%</p></div>
          <div className="stat-card"><p className="stat-label">Avg Duration</p><p className="stat-value">{stats.avg_duration_seconds.toFixed(1)}s</p></div>
          <div className="stat-card"><p className="stat-label">Failed</p><p className="stat-value text-red-600">{stats.failed}</p></div>
        </div>
      )}

      {/* Nodes */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold">Workflow Nodes ({workflow.nodes?.length || 0})</h2>
        </div>
        <div className="card-body">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-surface-500 border-b border-surface-100">
                  <th className="pb-3 font-medium">Name</th>
                  <th className="pb-3 font-medium">Type</th>
                  <th className="pb-3 font-medium">Position</th>
                </tr>
              </thead>
              <tbody>
                {workflow.nodes?.map((node: any) => (
                  <tr key={node.id} className="border-b border-surface-50 hover:bg-surface-50">
                    <td className="py-3 font-medium">{node.name}</td>
                    <td className="py-3"><span className="badge-info">{node.node_type}</span></td>
                    <td className="py-3 text-surface-500">({node.position_x}, {node.position_y})</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Recent Executions */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold">Recent Executions</h2>
          <Link to="/executions" className="text-sm text-primary-600 hover:text-primary-700">View all →</Link>
        </div>
        <div className="card-body">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-surface-500 border-b border-surface-100">
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Started</th>
                  <th className="pb-3 font-medium">Duration</th>
                  <th className="pb-3 font-medium">Error</th>
                </tr>
              </thead>
              <tbody>
                {recentExecs?.map((exec: any) => (
                  <tr key={exec.id} className="border-b border-surface-50 hover:bg-surface-50">
                    <td className="py-3">
                      <span className={`badge-${exec.status === 'completed' ? 'success' : exec.status === 'failed' ? 'error' : exec.status === 'running' ? 'info' : 'neutral'}`}>
                        {exec.status}
                      </span>
                    </td>
                    <td className="py-3 text-surface-500">{new Date(exec.started_at).toLocaleString()}</td>
                    <td className="py-3 text-surface-500">{exec.completed_at ? `${((new Date(exec.completed_at).getTime() - new Date(exec.started_at).getTime())/1000).toFixed(1)}s` : '-'}</td>
                    <td className="py-3 text-red-500 max-w-xs truncate">{exec.error_message || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}