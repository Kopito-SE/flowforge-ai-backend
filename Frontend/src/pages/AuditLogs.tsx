import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { accountsApi } from '../services/api';
import { Search, FileText } from 'lucide-react';

export function AuditLogs() {
  const [action, setAction] = useState('');
  const [search, setSearch] = useState('');

  const { data: logs } = useQuery({
    queryKey: ['audit-logs', action],
    queryFn: () => accountsApi.auditLogs({ action: action || undefined, limit: 100 }),
    refetchInterval: 15000,
  });

  const filtered = logs?.filter((l: any) =>
    l.actor?.toLowerCase().includes(search.toLowerCase()) ||
    l.action?.toLowerCase().includes(search.toLowerCase()) ||
    l.resource_name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Audit Logs</h1>
        <p className="text-surface-500 mt-1">Track all important actions across the system</p>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
          <input type="text" placeholder="Search logs..." className="input pl-10" value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="select w-48" value={action} onChange={e => setAction(e.target.value)}>
          <option value="">All Actions</option>
          <option value="workflow.created">Workflow Created</option>
          <option value="workflow.published">Workflow Published</option>
          <option value="workflow.deleted">Workflow Deleted</option>
          <option value="api_key.created">API Key Created</option>
          <option value="api_key.revoked">API Key Revoked</option>
          <option value="organization.created">Org Created</option>
          <option value="member.invited">Member Invited</option>
          <option value="role.assigned">Role Assigned</option>
        </select>
      </div>

      <div className="card">
        <div className="card-body p-0">
          {filtered?.length === 0 ? (
            <div className="text-center py-12 text-surface-500">
              <FileText className="w-12 h-12 mx-auto mb-3 text-surface-300" />
              <p>No audit logs found</p>
            </div>
          ) : (
            <div className="divide-y divide-surface-100">
              {filtered?.map((log: any) => (
                <div key={log.id} className="px-6 py-4 hover:bg-surface-50">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-surface-900">{log.actor}</span>
                        <span className="text-surface-500">performed</span>
                        <span className="badge-info">{log.action_display}</span>
                      </div>
                      {log.resource_name && (
                        <p className="text-sm text-surface-500 mt-1">on {log.resource_name}</p>
                      )}
                      {Object.keys(log.details || {}).length > 0 && (
                        <pre className="mt-2 text-xs text-surface-400 bg-surface-50 rounded p-2 max-w-2xl overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      )}
                    </div>
                    <span className="text-xs text-surface-400 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}