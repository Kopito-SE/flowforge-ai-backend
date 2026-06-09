import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { executionApi } from '../services/api';
import { ArrowLeft } from 'lucide-react';

export function ExecutionDetail() {
  const { id } = useParams();
  const { data: executions } = useQuery({
    queryKey: ['executions'],
    queryFn: () => executionApi.search({ limit: 1 }),
  });

  const exec = executions?.find((e: any) => e.id === id);

  if (!exec) return <div className="animate-pulse h-96 bg-surface-100 rounded-xl" />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/executions" className="p-2 rounded-lg hover:bg-surface-100">
          <ArrowLeft className="w-5 h-5 text-surface-500" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold">Execution Details</h1>
          <p className="text-surface-500 mt-1">ID: {exec.id}</p>
        </div>
        <span className={`badge-${exec.status === 'completed' ? 'success' : exec.status === 'failed' ? 'error' : exec.status === 'running' ? 'info' : 'neutral'}`}>
          {exec.status}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="stat-card">
          <p className="stat-label">Workflow</p>
          <p className="text-lg font-semibold mt-1">{exec.workflow}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Started</p>
          <p className="text-lg font-semibold mt-1">{new Date(exec.started_at).toLocaleString()}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Duration</p>
          <p className="text-lg font-semibold mt-1">
            {exec.completed_at ? `${((new Date(exec.completed_at).getTime() - new Date(exec.started_at).getTime())/1000).toFixed(1)}s` : '-'}
          </p>
        </div>
      </div>

      {exec.error_message && (
        <div className="card border-red-200 bg-red-50">
          <div className="card-body">
            <h3 className="font-semibold text-red-800 mb-2">Error Message</h3>
            <p className="text-red-600 text-sm font-mono">{exec.error_message}</p>
          </div>
        </div>
      )}
    </div>
  );
}