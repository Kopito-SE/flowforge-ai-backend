import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { aiApi } from '../services/api';
import { BrainCircuit, Send, Sparkles, MessageSquare } from 'lucide-react';
import toast from 'react-hot-toast';

export function AiPlayground() {
  const [description, setDescription] = useState('');
  const [classifyText, setClassifyText] = useState('');
  const [categories, setCategories] = useState('');
  const [result, setResult] = useState<any>(null);

  const generateMutation = useMutation({
    mutationFn: (desc: string) => aiApi.generateWorkflow(desc),
    onSuccess: (data) => {
      setResult(data);
      toast.success('Workflow generated!');
    },
    onError: (err: any) => {
      toast.error('Generation failed - AI integration not yet connected');
    },
  });

  const classifyMutation = useMutation({
    mutationFn: ({ text, cats }: any) => aiApi.classify(text, cats),
    onSuccess: (data) => {
      setResult(data);
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI Playground</h1>
        <p className="text-surface-500 mt-1">Experiment with AI-powered workflow features</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Generate Workflow */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-primary-600" />
              <h2 className="text-lg font-semibold">Generate Workflow</h2>
            </div>
          </div>
          <div className="card-body space-y-4">
            <p className="text-sm text-surface-600">Describe your automation in natural language and AI will create the workflow graph.</p>
            <textarea
              className="textarea h-32"
              placeholder='e.g., "When a lead signs up, send a welcome email, create a CRM contact, and notify the sales team on Slack"'
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
            <button
              onClick={() => generateMutation.mutate(description)}
              disabled={!description || generateMutation.isPending}
              className="btn-primary w-full"
            >
              <Sparkles className="w-4 h-4" />
              {generateMutation.isPending ? 'Generating...' : 'Generate Workflow'}
            </button>

            {result && result.nodes && (
              <div className="mt-4 p-4 bg-surface-50 rounded-lg">
                <h3 className="font-semibold mb-2">Generated Workflow</h3>
                <div className="space-y-2">
                  {result.nodes.map((node: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <div className="w-2 h-2 rounded-full bg-primary-500" />
                      <span className="font-medium">{node.name}</span>
                      <span className="badge-info">{node.node_type}</span>
                    </div>
                  ))}
                </div>
                {result.connections?.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-surface-200">
                    <p className="text-xs text-surface-500 font-medium mb-1">Connections:</p>
                    {result.connections.map((conn: any, i: number) => (
                      <p key={i} className="text-xs text-surface-500">{conn.source} → {conn.target}</p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Classify Text */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-amber-600" />
              <h2 className="text-lg font-semibold">Text Classification</h2>
            </div>
          </div>
          <div className="card-body space-y-4">
            <p className="text-sm text-surface-600">Classify text into categories using AI.</p>
            <textarea
              className="textarea h-20"
              placeholder="Enter text to classify..."
              value={classifyText}
              onChange={e => setClassifyText(e.target.value)}
            />
            <div>
              <label className="label">Categories (comma-separated)</label>
              <input
                type="text"
                className="input"
                placeholder="e.g., support, sales, spam"
                value={categories}
                onChange={e => setCategories(e.target.value)}
              />
            </div>
            <button
              onClick={() => classifyMutation.mutate({ text: classifyText, cats: categories.split(',').map(c => c.trim()).filter(Boolean) })}
              disabled={!classifyText || !categories}
              className="btn-primary w-full"
            >
              <Send className="w-4 h-4" /> Classify
            </button>

            {classifyMutation.data && (
              <div className="mt-4 p-4 bg-surface-50 rounded-lg">
                <h3 className="font-semibold mb-1">Classification Result</h3>
                <p className="text-sm">Category: <span className="font-medium text-primary-600">{classifyMutation.data.category}</span></p>
                <p className="text-sm">Confidence: <span className="font-medium">{(classifyMutation.data.confidence * 100).toFixed(0)}%</span></p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}