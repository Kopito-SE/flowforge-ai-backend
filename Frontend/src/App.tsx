import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { WorkflowList } from './pages/WorkflowList';
import { WorkflowBuilder } from './pages/WorkflowBuilder';
import { WorkflowDetail } from './pages/WorkflowDetail';
import { ExecutionList } from './pages/ExecutionList';
import { ExecutionDetail } from './pages/ExecutionDetail';
import { Integrations } from './pages/Integrations';
import { ApiKeys } from './pages/ApiKeys';
import { Organizations } from './pages/Organizations';
import { AuditLogs } from './pages/AuditLogs';
import { Monitoring } from './pages/Monitoring';
import { Alerts } from './pages/Alerts';
import { Events } from './pages/Events';
import { Settings } from './pages/Settings';
import { Templates } from './pages/Templates';
import { AiPlayground } from './pages/AiPlayground';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="workflows" element={<WorkflowList />} />
        <Route path="workflows/:id" element={<WorkflowDetail />} />
        <Route path="workflows/:id/builder" element={<WorkflowBuilder />} />
        <Route path="executions" element={<ExecutionList />} />
        <Route path="executions/:id" element={<ExecutionDetail />} />
        <Route path="integrations" element={<Integrations />} />
        <Route path="api-keys" element={<ApiKeys />} />
        <Route path="templates" element={<Templates />} />
        <Route path="organizations" element={<Organizations />} />
        <Route path="audit-logs" element={<AuditLogs />} />
        <Route path="monitoring" element={<Monitoring />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="events" element={<Events />} />
        <Route path="ai" element={<AiPlayground />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}