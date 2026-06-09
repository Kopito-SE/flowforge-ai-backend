import { useQuery } from '@tanstack/react-query';
import { monitoringApi, executionApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import {
  Activity, CheckCircle, XCircle, Clock, TrendingUp, AlertTriangle,
} from 'lucide-react';

export function Dashboard() {
  const [events, setEvents] = useState<any[]>([]);

  const { data: metrics } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => monitoringApi.dashboard(24),
    refetchInterval: 10000,
  });

  const { data: executions } = useQuery({
    queryKey: ['recent-executions'],
    queryFn: () => executionApi.search({ limit: 5 }),
    refetchInterval: 5000,
  });

  useWebSocket({
    url: `ws://${window.location.host}/ws/dashboard/`,
    onMessage: (data) => {
      if (data.type === 'dashboard_update') {
        setEvents(prev => [data.data, ...prev].slice(0, 20));
      }
    },
  });

  const stats = [
    {
      label: 'Total Executions',
      value: metrics?.total_executions ?? 0,
      icon: Activity,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
    },
    {
      label: 'Success Rate',
      value: `${metrics?.success_rate ?? 100}%`,
      icon: TrendingUp,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50',
    },
    {
      label: 'Failed',
      value: metrics?.failed ?? 0,
      icon: XCircle,
      color: 'text-red-600',
      bg: 'bg-red-50',
    },
    {
      label: 'Avg Duration',
      value: metrics ? `${(metrics.avg_duration_ms / 1000).toFixed(1)}s` : '0s',
      icon: Clock,
      color: 'text-amber-600',
      bg: 'bg-amber-50',
    },
  ];

  const chartData = [
    { name: 'Mon', success: 45, failed: 5 },
    { name: 'Tue', success: 52, failed: 3 },
    { name: 'Wed', success: 48, failed: 7 },
    { name: 'Thu', success: 60, failed: 2 },
    { name: 'Fri', success: 55, failed: 4 },
    { name: 'Sat', success: 40, failed: 1 },
    { name: 'Sun', success: 35, failed: 6 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-surface-900">Dashboard</h1>
        <p className="text-surface-500 mt-1">Real-time overview of your automation platform</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="stat-card">
              <div className="flex items-center justify-between">
                <div className={`p-2 rounded-lg ${stat.bg}`}>
                  <Icon className={`w-5 h-5 ${stat.color}`} />
                </div>
              </div>
              <p className="stat-value">{stat.value}</p>
              <p className="stat-label">{stat.label}</p>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Weekly Performance</h2>
            <span className="badge-neutral">Last 7 days</span>
          </div>
          <div className="card-body">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="success" fill="#2563eb" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="failed" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">Success Rate Trend</h2>
            <span className="badge-success">{metrics?.success_rate ?? 100}%</span>
          </div>
          <div className="card-body">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                  <YAxis stroke="#94a3b8" fontSize={12} />
                  <Tooltip />
                  <Line type="monotone" dataKey="success" stroke="#2563eb" strokeWidth={2} dot={{ fill: '#2563eb' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Executions */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold">Recent Executions</h2>
          <span className="text-sm text-surface-500">Latest 5</span>
        </div>
        <div className="card-body">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-surface-500 border-b border-surface-100">
                  <th className="pb-3 font-medium">Workflow</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Started</th>
                  <th className="pb-3 font-medium">Duration</th>
                  <th className="pb-3 font-medium">Retries</th>
                </tr>
              </thead>
              <tbody>
                {executions?.map((exec: any) => (
                  <tr key={exec.id} className="border-b border-surface-50 hover:bg-surface-50">
                    <td className="py-3 font-medium text-surface-900">{exec.workflow}</td>
                    <td className="py-3">
                      <span className={`badge-${exec.status === 'completed' ? 'success' : exec.status === 'failed' ? 'error' : exec.status === 'running' ? 'info' : 'neutral'}`}>
                        {exec.status}
                      </span>
                    </td>
                    <td className="py-3 text-surface-500">{new Date(exec.started_at).toLocaleString()}</td>
                    <td className="py-3 text-surface-500">
                      {exec.completed_at
                        ? `${((new Date(exec.completed_at).getTime() - new Date(exec.started_at).getTime()) / 1000).toFixed(1)}s`
                        : '-'}
                    </td>
                    <td className="py-3 text-surface-500">{exec.retry_count}</td>
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