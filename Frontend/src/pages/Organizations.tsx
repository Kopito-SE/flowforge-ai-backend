import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountsApi } from '../services/api';
import { Users, Plus, Mail } from 'lucide-react';
import toast from 'react-hot-toast';

export function Organizations() {
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (data: any) => accountsApi.organizations.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] });
      toast.success(`Organization "${data.name}" created`);
      setShowCreate(false);
      setName('');
      setDescription('');
    },
  });

  const inviteMutation = useMutation({
    mutationFn: ({ slug, data }: any) => accountsApi.organizations.invite(slug, data),
    onSuccess: () => {
      toast.success('Invitation sent');
      setInviteEmail('');
    },
  });

  const queryClient = useQueryClient();

  const { data: orgs } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => accountsApi.organizations.list?.() || Promise.resolve([]),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Organizations</h1>
          <p className="text-surface-500 mt-1">Manage teams and organization settings</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          <Plus className="w-4 h-4" /> Create Organization
        </button>
      </div>

      {showCreate && (
        <div className="card p-6 border-primary-200 bg-primary-50">
          <div className="space-y-4">
            <h3 className="font-semibold">Create New Organization</h3>
            <div>
              <label className="label">Name</label>
              <input type="text" className="input" placeholder="e.g., Acme Corp" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div>
              <label className="label">Description</label>
              <textarea className="textarea" placeholder="Organization description..." value={description} onChange={e => setDescription(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <button onClick={() => createMutation.mutate({ name, description })} className="btn-primary">Create</button>
              <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-body">
          <div className="text-center py-12 text-surface-500">
            <Users className="w-12 h-12 mx-auto mb-3 text-surface-300" />
            <p>No organizations yet. Create one to start collaborating.</p>
          </div>
        </div>
      </div>
    </div>
  );
}