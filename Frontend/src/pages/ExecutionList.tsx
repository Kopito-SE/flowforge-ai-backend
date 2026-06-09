import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { executionApi, workflowApi } from '../services/api';
import { Search, XCircle, Play, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

export function ExecutionList() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data: executions, isLoading } = useQuery({
    queryKey: ['executions', statusFilter],
    queryFn: () => executionApi.search({ status: statusFilter || undefined, limit: 50 }),
    refetchInterval: 5000,
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => executionApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      toast.success('Execution cancelled');
    },
  });

  const resumeMutation = useMutation({
    mutationFn: (id: string) => executionApi.resume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      toast.success('Execution resumed');
    },
  });

  const getStatusBadge = (status: string) => {
    const map: Record<string, string> = {
      pending: 'badge-neutral', running: 'badge-info', completed: 'badge-success', failed: 'badge-error', cancelled: 'badge-warning',
    };
    return map[status] || 'badge-neutral';
  };

  const filtered = executions?.filter((e: any) =>
    e.workflow?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Executions</h1>
        <p className="text-surface-500 mt-1">Monitor and manage workflow executions</p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
          <input type="text" placeholder="Search by workflow name..." className="input pl-10" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="select w-40" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-surface-500 border-b border-surface-100">
                <th className="px-6 py-4 font-medium">Workflow</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Started</th>
                <th className="px-6 py-4 font-medium">Duration</th>
                <th className="px-6 py-4 font-medium">Retries</th>
                <th className="px-6 py-4 font-medium">Error</th>
                <th className="px-6 py-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={7} className="px-6 py-12 text-center text-surface-500">Loading...</td></tr>
              ) : filtered?.length === 0 ? (
                <tr><td colSpan={7} className="px-6 py-12 text-center text-surface-500">No executions found</td></tr>
              ) : (
                filtered?.map((exec: any) => (
                  <tr key={exec.id} className="border-b border-surface-50 hover:bg-surface-50">
                    <td className="px-6 py-4 font-medium">{exec.workflow}</td>
                    <td className="px-6 py-4">
                      <span className={getStatusBadge(exec.status)}>{exec.status}</span>
                    </td>
                    <td className="px-6 py-4 text-surface-500">{new Date(exec.started_at).toLocaleString()}</td>
                    <td className="px-6 py-4 text-surface-500">
                      {exec.completed_at
                        ? `${((new Date(exec.completed_at).getTime() - new Date(exec.started_at).getTime())/1000).toFixed(1)}s`
                        : exec.status === 'running' ? 'Running...' : '-'}
                    </td>
                    <td className="px-6 py-4 text-surface-500">{exec.retry_count}</td>
                    <td className="px-6 py-4 text-red-500 max-w-[200px] truncate">{exec.error_message || '-'}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        {(exec.status === 'running' || exec.status === 'pending') && (
                          <button onClick={() => cancelMutation.mutate(exec.id)} className="p-1.5 rounded hover:bg-red-50 text-red-500" title="Cancel">
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}
                        {exec.status === 'failed' && (
                          <button onClick={() => resumeMutation.mutate(exec.id)} className="p-1.5 rounded hover:bg-emerald-50 text-emerald-600" title="Resume">
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}