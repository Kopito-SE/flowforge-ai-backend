import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountsApi } from '../services/api';
import { Plus, Copy, RotateCcw, XCircle, Key, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';

export function ApiKeys() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [expiresIn, setExpiresIn] = useState('90');
  const [newKey, setNewKey] = useState<string | null>(null);

  const { data: keys } = useQuery({
    queryKey: ['api-keys'],
    queryFn: accountsApi.apiKeys.list,
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => accountsApi.apiKeys.create(data),
    onSuccess: (data) => {
      setNewKey(data.key);
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      toast.success('API key created');
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => accountsApi.apiKeys.revoke(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      toast.success('API key revoked');
    },
  });

  const rotateMutation = useMutation({
    mutationFn: (id: string) => accountsApi.apiKeys.rotate(id),
    onSuccess: (data) => {
      setNewKey(data.key);
      queryClient.invalidateQueries({ queryKey: ['api-keys'] });
      toast.success('API key rotated');
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">API Keys</h1>
          <p className="text-surface-500 mt-1">Manage API keys for programmatic access</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4" /> Create Key
        </button>
      </div>

      {/* Create Key Modal */}
      {showCreate && (
        <div className="card p-6 border-primary-200 bg-primary-50">
          {newKey ? (
            <div>
              <h3 className="font-semibold text-emerald-700 mb-2">API Key Created!</h3>
              <p className="text-sm text-surface-600 mb-3">Copy this key now. It won't be shown again.</p>
              <div className="flex gap-2">
                <code className="flex-1 p-3 bg-white rounded-lg border border-emerald-200 font-mono text-sm break-all">
                  {newKey}
                </code>
                <button onClick={() => { navigator.clipboard.writeText(newKey); toast.success('Copied!'); }} className="btn-secondary btn-sm">
                  <Copy className="w-4 h-4" />
                </button>
              </div>
              <button onClick={() => { setShowCreate(false); setNewKey(null); }} className="btn-primary mt-3">
                Done
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <h3 className="font-semibold">Create New API Key</h3>
              <div>
                <label className="label">Name</label>
                <input type="text" className="input" placeholder="e.g., Production API" value={name} onChange={e => setName(e.target.value)} />
              </div>
              <div>
                <label className="label">Expires In</label>
                <select className="select" value={expiresIn} onChange={e => setExpiresIn(e.target.value)}>
                  <option value="30">30 days</option>
                  <option value="90">90 days</option>
                  <option value="365">1 year</option>
                  <option value="">No expiration</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button onClick={() => createMutation.mutate({ name, expires_in_days: expiresIn ? parseInt(expiresIn) : undefined })} className="btn-primary">
                  Create Key
                </button>
                <button onClick={() => { setShowCreate(false); setNewKey(null); setName(''); }} className="btn-secondary">
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Keys List */}
      <div className="card">
        <div className="card-body">
          {keys?.length === 0 ? (
            <div className="text-center py-12 text-surface-500">
              <Key className="w-12 h-12 mx-auto mb-3 text-surface-300" />
              <p>No API keys yet. Create one to get started.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {keys?.map((key: any) => (
                <div key={key.id} className="flex items-center justify-between p-4 rounded-lg border border-surface-200 hover:border-surface-300 transition-colors">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{key.name}</span>
                      <span className={`badge-${key.status === 'active' ? 'success' : key.status === 'expired' ? 'warning' : 'error'}`}>
                        {key.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <code className="text-sm text-surface-500 font-mono">{key.key_prefix}...</code>
                      <span className="text-xs text-surface-400">Created {new Date(key.created_at).toLocaleDateString()}</span>
                      {key.expires_at && <span className="text-xs text-surface-400">Expires {new Date(key.expires_at).toLocaleDateString()}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {key.status === 'active' && (
                      <>
                        <button onClick={() => rotateMutation.mutate(key.id)} className="p-2 rounded-lg hover:bg-amber-50 text-amber-600" title="Rotate">
                          <RotateCcw className="w-4 h-4" />
                        </button>
                        <button onClick={() => revokeMutation.mutate(key.id)} className="p-2 rounded-lg hover:bg-red-50 text-red-500" title="Revoke">
                          <XCircle className="w-4 h-4" />
                        </button>
                      </>
                    )}
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