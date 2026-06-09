import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { monitoringApi } from '../services/api';
import { Bell, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export function Alerts() {
  const queryClient = useQueryClient();
  const { data: alerts } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => monitoringApi.alerts({ limit: 50 }),
    refetchInterval: 10000,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (id: string) => monitoringApi.acknowledgeAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      toast.success('Alert acknowledged');
    },
  });

  const getSeverityColor = (severity: string) => {
    const map: Record<string, string> = {
      critical: 'badge-error',
      warning: 'badge-warning',
      info: 'badge-info',
    };
    return map[severity] || 'badge-neutral';
  };

  const getStatusColor = (status: string) => {
    const map: Record<string, string> = {
      firing: 'badge-error',
      acknowledged: 'badge-warning',
      resolved: 'badge-success',
    };
    return map[status] || 'badge-neutral';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Alerts</h1>
        <p className="text-surface-500 mt-1">Monitor and manage system alerts</p>
      </div>

      <div className="card">
        <div className="card-body">
          {alerts?.length === 0 ? (
            <div className="text-center py-12 text-surface-500">
              <Bell className="w-12 h-12 mx-auto mb-3 text-surface-300" />
              <p>No alerts. All systems are running smoothly.</p>
            </div>
          ) : (
            <div className="divide-y divide-surface-100">
              {alerts?.map((alert: any) => (
                <div key={alert.id} className="py-4 flex items-start gap-4">
                  <div className={`p-2 rounded-lg ${alert.severity === 'critical' ? 'bg-red-50' : alert.severity === 'warning' ? 'bg-amber-50' : 'bg-blue-50'}`}>
                    <Bell className={`w-5 h-5 ${alert.severity === 'critical' ? 'text-red-600' : alert.severity === 'warning' ? 'text-amber-600' : 'text-blue-600'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium">{alert.rule}</span>
                      <span className={getSeverityColor(alert.severity)}>{alert.severity}</span>
                      <span className={getStatusColor(alert.status)}>{alert.status}</span>
                    </div>
                    <p className="text-sm text-surface-600 mt-1">{alert.message}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-surface-500">
                      <span>{new Date(alert.created_at).toLocaleString()}</span>
                      {alert.metric_value != null && <span>Value: {alert.metric_value}</span>}
                      {alert.threshold != null && <span>Threshold: {alert.threshold}</span>}
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    {alert.status === 'firing' && (
                      <button onClick={() => acknowledgeMutation.mutate(alert.id)} className="btn-secondary btn-sm">
                        <CheckCircle className="w-4 h-4" /> Acknowledge
                      </button>
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