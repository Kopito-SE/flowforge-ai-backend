import { useQuery } from '@tanstack/react-query';
import { workflowApi } from '../services/api';
import { LayoutTemplate, Search } from 'lucide-react';
import { useState } from 'react';

export function Templates() {
  const [category, setCategory] = useState('');

  const { data: templates } = useQuery({
    queryKey: ['templates', category],
    queryFn: () => workflowApi.templates(category || undefined),
  });

  const categories = [
    { name: '', label: 'All' },
    { name: 'marketing', label: 'Marketing' },
    { name: 'sales', label: 'Sales' },
    { name: 'support', label: 'Support' },
    { name: 'engineering', label: 'Engineering' },
    { name: 'finance', label: 'Finance' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Workflow Templates</h1>
        <p className="text-surface-500 mt-1">Pre-built automation templates to get started quickly</p>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {categories.map((cat) => (
          <button
            key={cat.name}
            onClick={() => setCategory(cat.name)}
            className={`btn-sm ${category === cat.name ? 'btn-primary' : 'btn-secondary'}`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates?.map((template: any) => (
          <div key={template.id} className="card p-6 hover:shadow-md transition-all cursor-pointer">
            <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center mb-4">
              <LayoutTemplate className="w-5 h-5 text-primary-600" />
            </div>
            <h3 className="font-semibold mb-1">{template.name}</h3>
            <p className="text-sm text-surface-500 mb-3 line-clamp-2">{template.description}</p>
            <div className="flex items-center gap-2">
              <span className="badge-info">{template.category}</span>
              <span className="text-xs text-surface-400">Created {new Date(template.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}