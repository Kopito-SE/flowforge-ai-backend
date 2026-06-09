import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { workflowApi } from '../services/api';
import { Plus, Search, MoreVertical, Play, Copy, Download, Upload, Archive } from 'lucide-react';
import toast from 'react-hot-toast';

export function WorkflowList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');

  const { data: workflows, isLoading } = useQuery({
    queryKey: ['workflows'],
    queryFn: workflowApi.list,
    refetchInterval: 10000,
  });

  const publishMutation = useMutation({
    mutationFn: (id: string) => workflowApi.publish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      toast.success('Workflow published');
    },
  });

  const archiveMutation = useMutation({
    mutationFn: (id: string) => workflowApi.archive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      toast.success('Workflow archived');
    },
  });

  const cloneMutation = useMutation({
    mutationFn: (id: string) => workflowApi.clone(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      toast.success('Workflow cloned');
    },
  });

  const filtered = workflows?.filter((w: any) =>
    w.name.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusBadge = (status: string) => {
    const map: Record<string, string> = {
      draft: 'badge-neutral',
      active: 'badge-success',
      disabled: 'badge-warning',
      published: 'badge-info',
      archived: 'badge-neutral',
    };
    return map[status] || 'badge-neutral';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-surface-900">Workflows</h1>
          <p className="text-surface-500 mt-1">Create and manage your automation workflows</p>
        </div>
        <button className="btn-primary" onClick={() => navigate('/workflows/new')}>
          <Plus className="w-4 h-4" />
          New Workflow
        </button>
      </div>

      {/* Search & Filter */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
          <input
            type="text"
            placeholder="Search workflows..."
            className="input pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Workflow Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-4 bg-surface-200 rounded w-3/4 mb-3" />
              <div className="h-3 bg-surface-100 rounded w-1/2 mb-4" />
              <div className="flex gap-2">
                <div className="h-5 bg-surface-100 rounded w-16" />
                <div className="h-5 bg-surface-100 rounded w-16" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered?.map((workflow: any) => (
            <div key={workflow.id} className="card hover:shadow-md transition-all">
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <Link to={`/workflows/${workflow.id}`} className="hover:text-primary-600">
                    <h3 className="font-semibold text-surface-900">{workflow.name}</h3>
                  </Link>
                  <div className="relative group">
                    <button className="p-1 rounded hover:bg-surface-100">
                      <MoreVertical className="w-4 h-4 text-surface-400" />
                    </button>
                    <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg border border-surface-200 shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                      <div className="py-1">
                        <button onClick={() => navigate(`/workflows/${workflow.id}/builder`)} className="w-full px-4 py-2 text-left text-sm hover:bg-surface-50 flex items-center gap-2">
                          <Play className="w-4 h-4" /> Open Builder
                        </button>
                        <button onClick={() => cloneMutation.mutate(workflow.id)} className="w-full px-4 py-2 text-left text-sm hover:bg-surface-50 flex items-center gap-2">
                          <Copy className="w-4 h-4" /> Clone
                        </button>
                        <button onClick={() => workflowApi.export(workflow.id).then(d => { const blob = new Blob([JSON.stringify(d, null, 2)], {type: 'application/json'}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `${workflow.name}.json`; a.click(); })} className="w-full px-4 py-2 text-left text-sm hover:bg-surface-50 flex items-center gap-2">
                          <Download className="w-4 h-4" /> Export
                        </button>
                        {workflow.publication_status === 'draft' && (
                          <button onClick={() => publishMutation.mutate(workflow.id)} className="w-full px-4 py-2 text-left text-sm hover:bg-surface-50 flex items-center gap-2">
                            <Upload className="w-4 h-4" /> Publish
                          </button>
                        )}
                        {workflow.publication_status === 'published' && (
                          <button onClick={() => archiveMutation.mutate(workflow.id)} className="w-full px-4 py-2 text-left text-sm hover:bg-surface-50 flex items-center gap-2">
                            <Archive className="w-4 h-4" /> Archive
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
                {workflow.description && (
                  <p className="text-sm text-surface-500 mb-4 line-clamp-2">{workflow.description}</p>
                )}
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={getStatusBadge(workflow.publication_status)}>
                    {workflow.publication_status}
                  </span>
                  <span className={getStatusBadge(workflow.status)}>
                    {workflow.status}
                  </span>
                  <span className="badge-neutral">v{workflow.version}</span>
                  <span className="badge-neutral">{workflow.node_count} nodes</span>
                </div>
              </div>
              <div className="px-6 py-3 bg-surface-50 border-t border-surface-100 rounded-b-xl">
                <div className="flex items-center justify-between text-xs text-surface-500">
                  <span>Created {new Date(workflow.created_at).toLocaleDateString()}</span>
                  <Link to={`/workflows/${workflow.id}`} className="text-primary-600 hover:text-primary-700 font-medium">
                    View Details →
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}