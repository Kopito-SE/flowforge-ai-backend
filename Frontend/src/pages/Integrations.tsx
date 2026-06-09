import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { integrationsApi } from '../services/api';
import { useState } from 'react';
import { Plus, Puzzle, ExternalLink, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

const providers = [
  { name: 'SendGrid', category: 'email', icon: '✉️', color: 'bg-blue-50 text-blue-600' },
  { name: 'Mailgun', category: 'email', icon: '📧', color: 'bg-orange-50 text-orange-600' },
  { name: 'Twilio', category: 'messaging', icon: '📱', color: 'bg-red-50 text-red-600' },
  { name: 'Slack', category: 'messaging', icon: '💬', color: 'bg-purple-50 text-purple-600' },
  { name: 'Discord', category: 'messaging', icon: '🎮', color: 'bg-indigo-50 text-indigo-600' },
  { name: 'HubSpot', category: 'crm', icon: '📊', color: 'bg-orange-50 text-orange-600' },
  { name: 'Salesforce', category: 'crm', icon: '☁️', color: 'bg-blue-50 text-blue-600' },
  { name: 'Google Sheets', category: 'google', icon: '📗', color: 'bg-emerald-50 text-emerald-600' },
  { name: 'Gmail', category: 'google', icon: '📬', color: 'bg-red-50 text-red-600' },
  { name: 'Slack', category: 'slack', icon: '💬', color: 'bg-purple-50 text-purple-600' },
  { name: 'Discord', category: 'slack', icon: '🎮', color: 'bg-indigo-50 text-indigo-600' },
  { name: 'Custom Webhook', category: 'webhook', icon: '🔗', color: 'bg-surface-100 text-surface-600' },
];

export function Integrations() {
  const { data: integrations } = useQuery({
    queryKey: ['integrations'],
    queryFn: integrationsApi.list,
  });

  const categories = integrations?.reduce((acc: any, i: any) => {
    acc[i.category] = acc[i.category] || [];
    acc[i.category].push(i);
    return acc;
  }, {}) || {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Integrations</h1>
        <p className="text-surface-500 mt-1">Connect your favorite tools and services</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {providers.map((provider) => (
          <div key={provider.name} className="card p-6 hover:shadow-md transition-all cursor-pointer group">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl ${provider.color}`}>
                {provider.icon}
              </div>
              <div className="flex-1">
                <h3 className="font-semibold">{provider.name}</h3>
                <p className="text-xs text-surface-500 capitalize">{provider.category}</p>
              </div>
              <ExternalLink className="w-4 h-4 text-surface-300 group-hover:text-primary-600 transition-colors" />
            </div>
          </div>
        ))}
      </div>

      {/* Connected Integrations */}
      {integrations?.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Connected Integrations</h2>
          </div>
          <div className="card-body">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-surface-500 border-b border-surface-100">
                    <th className="pb-3 font-medium">Name</th>
                    <th className="pb-3 font-medium">Provider</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Last Used</th>
                  </tr>
                </thead>
                <tbody>
                  {integrations.map((i: any) => (
                    <tr key={i.id} className="border-b border-surface-50 hover:bg-surface-50">
                      <td className="py-3 font-medium">{i.name}</td>
                      <td className="py-3">{i.provider_display}</td>
                      <td className="py-3">
                        <span className={i.is_connected ? 'badge-success' : 'badge-neutral'}>
                          {i.is_connected ? 'Connected' : 'Disconnected'}
                        </span>
                      </td>
                      <td className="py-3 text-surface-500">{i.last_used_at ? new Date(i.last_used_at).toLocaleDateString() : 'Never'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}