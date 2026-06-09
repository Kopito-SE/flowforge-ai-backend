export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'active' | 'disabled';
  publication_status: 'draft' | 'published' | 'archived';
  version: number;
  is_active: boolean;
  node_count: number;
  execution_count?: number;
  nodes?: WorkflowNode[];
  created_at: string;
  updated_at: string;
  published_at?: string;
}

export interface WorkflowNode {
  id: string;
  name: string;
  node_type: NodeType;
  configuration: Record<string, any>;
  position_x: number;
  position_y: number;
  ui_metadata: Record<string, any>;
  connections: NodeConnection[];
}

export type NodeType =
  | 'trigger'
  | 'condition'
  | 'email'
  | 'webhook'
  | 'delay'
  | 'event_trigger'
  | 'schedule_trigger'
  | 'ai_prompt'
  | 'ai_condition'
  | 'ai_agent';

export interface NodeConnection {
  target_id: string;
  label?: string;
}

export interface WorkflowExecution {
  id: string;
  workflow: string;
  workflow_id: string;
  status: ExecutionStatus;
  current_node?: string;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  retry_count: number;
  duration_ms?: number;
  memory_usage_mb?: number;
}

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface DashboardMetrics {
  total_executions: number;
  failed: number;
  completed: number;
  running: number;
  success_rate: number;
  avg_duration_ms: number;
  period_hours: number;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  slug: string;
  category: string;
  description: string;
  created_at: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  key?: string;
  status: 'active' | 'revoked' | 'expired';
  last_used_at?: string;
  created_at: string;
  expires_at?: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description: string;
  tier: string;
  member_count: number;
  created_at: string;
}

export interface OrganizationMember {
  user_id: string;
  username: string;
  email: string;
  role: string;
  joined_at?: string;
}

export interface AuditLogEntry {
  id: string;
  actor: string;
  action: string;
  action_display: string;
  resource_type: string;
  resource_name: string;
  details: Record<string, any>;
  created_at: string;
}

export interface Alert {
  id: string;
  rule: string;
  severity: 'critical' | 'warning' | 'info';
  status: 'firing' | 'acknowledged' | 'resolved';
  message: string;
  metric_value?: number;
  threshold?: number;
  created_at: string;
  acknowledged_at?: string;
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, { status: string; response_time_ms?: number; error?: string }>;
}

export interface Integration {
  id: string;
  name: string;
  provider: string;
  provider_display: string;
  category: string;
  is_connected: boolean;
  is_active: boolean;
  last_used_at?: string;
  error_count: number;
  created_at: string;
}

export interface WebhookEndpoint {
  id: string;
  name: string;
  url_path: string;
  provider: string;
}

export interface EventItem {
  event_id: string;
  event_type: string;
  event_version: string;
  payload: Record<string, any>;
  source: string;
  correlation_id: string;
  created_at: string;
}

export interface EventReplayJob {
  job_id: string;
  event_type: string;
  status: string;
  events_processed: number;
  events_failed: number;
  total_events: number;
  created_at: string;
  completed_at?: string;
}

export interface ExecutionStats {
  total: number;
  completed: number;
  failed: number;
  cancelled: number;
  success_rate: number;
  avg_duration_seconds: number;
  period_days: number;
}

export interface Permission {
  permissions: string[];
}