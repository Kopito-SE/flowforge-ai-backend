import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { eventsApi } from '../services/api';
import { Zap, Search, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

export function Events() {
  const [eventType, setEventType] = useState('');
  const [replayEventType, setReplayEventType] = useState('');

  const { data: events } = useQuery({
    queryKey: ['events', eventType],
    queryFn: () => eventsApi.list({ event_type: eventType || undefined, limit: 50 }),
    refetchInterval: 10000,
  });

  const replayMutation = useMutation({
    mutationFn: (data: any) => eventsApi.replay(data),
    onSuccess: (data) => {
      toast.success(`Replay job created: ${data.event_type}`);
      setReplayEventType('');
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Events</h1>
        <p className="text-surface-500 mt-1">Browse and replay historical events</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold">Event Log</h2>
              <select className="select w-48" value={eventType} onChange={e => setEventType(e.target.value)}>
                <option value="">All Events</option>
                <option value="user.created">User Created</option>
                <option value="workflow.executed">Workflow Executed</option>
                <option value="workflow.created">Workflow Created</option>
                <option value="integration.connected">Integration Connected</option>
              </select>
            </div>
            <div className="card-body p-0">
              <div className="divide-y divide-surface-100">
                {events?.map((event: any) => (
                  <div key={event.event_id} className="px-6 py-3 hover:bg-surface-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-amber-500" />
                        <span className="font-medium font-mono text-sm">{event.event_type}</span>
                        <span className="badge-neutral">v{event.event_version}</span>
                      </div>
                      <span className="text-xs text-surface-400">{new Date(event.created_at).toLocaleString()}</span>
                    </div>
                    <div className="mt-1 text-xs text-surface-500 font-mono truncate max-w-2xl">
                      {JSON.stringify(event.payload).slice(0, 200)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div>
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold">Replay Events</h2>
            </div>
            <div className="card-body space-y-4">
              <p className="text-sm text-surface-600">Replay historical events to re-trigger workflows.</p>
              <div>
                <label className="label">Event Type</label>
                <select className="select" value={replayEventType} onChange={e => setReplayEventType(e.target.value)}>
                  <option value="">Select event type...</option>
                  <option value="user.created">User Created</option>
                  <option value="workflow.executed">Workflow Executed</option>
                  <option value="workflow.created">Workflow Created</option>
                </select>
              </div>
              <button
                onClick={() => replayMutation.mutate({ event_type: replayEventType })}
                disabled={!replayEventType}
                className="btn-primary w-full"
              >
                <RefreshCw className="w-4 h-4" /> Start Replay
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}