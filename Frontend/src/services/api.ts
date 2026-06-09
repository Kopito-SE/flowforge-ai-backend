import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// =========================
// Workflows
// =========================
export const workflowApi = {
  list: () => API.get('/workflows/').then(r => r.data),
  get: (id: string) => API.get(`/workflows/${id}/`).then(r => r.data),
  trigger: (event_type: string, payload: any) =>
    API.post('/trigger-workflow/', { event_type, payload }).then(r => r.data),
  clone: (id: string, name?: string) =>
    API.post(`/workflows/${id}/clone/`, { name }).then(r => r.data),
  export: (id: string) => API.get(`/workflows/${id}/export/`).then(r => r.data),
  import: (data: any) => API.post('/workflows/import/', data).then(r => r.data),
  publish: (id: string) => API.post(`/workflows/${id}/publish/`).then(r => r.data),
  archive: (id: string) => API.post(`/workflows/${id}/archive/`).then(r => r.data),
  templates: (category?: string) =>
    API.get('/workflow-templates/', { params: { category } }).then(r => r.data),
};

// =========================
// Executions
// =========================
export const executionApi = {
  search: (params?: any) => API.get('/executions/search/', { params }).then(r => r.data),
  cancel: (id: string) => API.post(`/executions/${id}/cancel/`).then(r => r.data),
  resume: (id: string) => API.post(`/executions/${id}/resume/`).then(r => r.data),
  stats: (workflow_id: string, days?: number) =>
    API.get('/executions/stats/', { params: { workflow_id, days } }).then(r => r.data),
};

// =========================
// Monitoring
// =========================
export const monitoringApi = {
  dashboard: (hours?: number) =>
    API.get('/monitoring/dashboard/', { params: { hours } }).then(r => r.data),
  health: () => API.get('/monitoring/health/').then(r => r.data),
  systemMetrics: () => API.get('/monitoring/system-metrics/').then(r => r.data),
  alerts: (params?: any) => API.get('/monitoring/alerts/', { params }).then(r => r.data),
  acknowledgeAlert: (id: string) =>
    API.post(`/monitoring/alerts/${id}/acknowledge/`).then(r => r.data),
};

// =========================
// Accounts
// =========================
export const accountsApi = {
  apiKeys: {
    list: () => API.get('/api-keys/').then(r => r.data),
    create: (data: any) => API.post('/api-keys/create/', data).then(r => r.data),
    revoke: (id: string) => API.post(`/api-keys/${id}/revoke/`).then(r => r.data),
    rotate: (id: string) => API.post(`/api-keys/${id}/rotate/`).then(r => r.data),
  },
  organizations: {
    create: (data: any) => API.post('/organizations/create/', data).then(r => r.data),
    get: (slug: string) => API.get(`/organizations/${slug}/`).then(r => r.data),
    invite: (slug: string, data: any) =>
      API.post(`/organizations/${slug}/invite/`, data).then(r => r.data),
    members: (slug: string) => API.get(`/organizations/${slug}/members/`).then(r => r.data),
  },
  auditLogs: (params?: any) => API.get('/audit-logs/', { params }).then(r => r.data),
  permissions: () => API.get('/permissions/').then(r => r.data),
  roles: {
    assign: (data: any) => API.post('/roles/assign/', data).then(r => r.data),
    revoke: (data: any) => API.post('/roles/revoke/', data).then(r => r.data),
  },
};

// =========================
// Events
// =========================
export const eventsApi = {
  list: (params?: any) => API.get('/events/', { params }).then(r => r.data),
  replay: (data: any) => API.post('/events/replay/', data).then(r => r.data),
  replayStatus: (jobId: string) => API.get(`/events/replay/${jobId}/`).then(r => r.data),
};

// =========================
// Integrations
// =========================
export const integrationsApi = {
  list: () => API.get('/integrations/').then(r => r.data),
  connect: (data: any) => API.post('/integrations/connect/', data).then(r => r.data),
  webhooks: {
    register: (data: any) => API.post('/webhooks/register/', data).then(r => r.data),
  },
};

// =========================
// AI
// =========================
export const aiApi = {
  generateWorkflow: (description: string) =>
    API.post('/ai/generate-workflow/', { description }).then(r => r.data),
  classify: (text: string, categories: string[]) =>
    API.post('/ai/classify/', { text, categories }).then(r => r.data),
  extractEntities: (text: string, entity_types?: string[]) =>
    API.post('/ai/extract-entities/', { text, entity_types }).then(r => r.data),
};

export default API;