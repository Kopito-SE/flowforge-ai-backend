import { useQuery } from '@tanstack/react-query';
import { monitoringApi } from '../services/api';
import { Activity, Database, Cpu, Server, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

export function Monitoring() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: monitoringApi.health,
    refetchInterval: 15000,
  });

  const { data: systemMetrics } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: monitoringApi.systemMetrics,
    refetchInterval: 10000,
  });

  const checks = health?.checks || {};
  const components = [
    { key: 'redis', label: 'Redis', icon: Database },
    { key: 'database', label: 'Database', icon: Server },
    { key: 'celery', label: 'Celery Workers', icon: Cpu },
    { key: 'channels', label: 'WebSocket Channels', icon: Activity },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Monitoring</h1>
        <p className="text-surface-500 mt-1">System health, metrics, and performance monitoring</p>
      </div>

      {/* Overall Status */}
      <div className={`card p-6 ${health?.status === 'healthy' ? 'border-emerald-200 bg-emerald-50' : 'border-red-200 bg-red-50'}`}>
        <div className="flex items-center gap-3">
          {health?.status === 'healthy' ? (
            <CheckCircle className="w-8 h-8 text-emerald-600" />
          ) : (
            <XCircle className="w-8 h-8 text-red-600" />
          )}
          <div>
            <h2 className="text-lg font-semibold capitalize">{health?.status || 'Checking...'}</h2>
            <p className="text-sm text-surface-600">Overall system status</p>
          </div>
        </div>
      </div>

      {/* Component Health */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {components.map(({ key, label, icon: Icon }) => {
          const check = checks[key];
          return (
            <div key={key} className="card p-6">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-lg ${check?.status === 'healthy' ? 'bg-emerald-50' : 'bg-red-50'}`}>
                  <Icon className={`w-6 h-6 ${check?.status === 'healthy' ? 'text-emerald-600' : 'text-red-600'}`} />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold">{label}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`badge-${check?.status === 'healthy' ? 'success' : 'error'}`}>
                      {check?.status || 'Unknown'}
                    </span>
                    {check?.response_time_ms && (
                      <span className="text-xs text-surface-500">{check.response_time_ms.toFixed(0)}ms</span>
                    )}
                  </div>
                  {check?.error && (
                    <p className="text-xs text-red-500 mt-1">{check.error}</p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* System Metrics */}
      {systemMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="stat-card">
            <p className="stat-label">Queue Depth</p>
            <p className="stat-value">{systemMetrics.queue_depth}</p>
            <p className="stat-change text-surface-500">Pending tasks in queue</p>
          </div>
          <div className="stat-card">
            <p className="stat-label">Open Circuit Breakers</p>
            <p className="stat-value text-red-600">{systemMetrics.open_circuit_breakers}</p>
            <p className="stat-change text-surface-500">Services with circuit open</p>
          </div>
          <div className="stat-card">
            <p className="stat-label">Recent Failures (1h)</p>
            <p className="stat-value text-amber-600">{systemMetrics.recent_failures_1h}</p>
            <p className="stat-change text-surface-500">Failed executions in last hour</p>
          </div>
        </div>
      )}
    </div>
  );
}