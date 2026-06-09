export function WorkflowBuilder() {
  return (
    <div className="h-[calc(100vh-8rem)] -m-4 lg:-m-6">
      <div className="h-full bg-white flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-surface-900 mb-2">Visual Workflow Builder</h2>
          <p className="text-surface-500 mb-6">Drag and drop nodes to build your automation workflow. This builder integrates with React Flow for a seamless visual experience.</p>
          <div className="space-y-3 text-left">
            <h3 className="font-medium text-surface-700">Available Node Types:</h3>
            <ul className="space-y-2">
              {[
                { name: 'Trigger', desc: 'Start workflow manually or on schedule' },
                { name: 'Condition', desc: 'Branch logic based on data values' },
                { name: 'Email', desc: 'Send emails via SendGrid/Mailgun' },
                { name: 'Webhook', desc: 'Make HTTP requests to external APIs' },
                { name: 'Delay', desc: 'Wait for a specified duration' },
                { name: 'AI Prompt', desc: 'Execute AI prompts (GPT-4, Claude)' },
                { name: 'AI Agent', desc: 'Autonomous AI agents with tools' },
              ].map((node) => (
                <li key={node.name} className="flex items-center gap-3 p-2 rounded-lg bg-surface-50">
                  <div className="w-2 h-2 rounded-full bg-primary-500" />
                  <div>
                    <p className="text-sm font-medium text-surface-700">{node.name}</p>
                    <p className="text-xs text-surface-500">{node.desc}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}