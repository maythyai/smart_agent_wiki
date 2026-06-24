import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

interface TemplateInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  variables: string[];
}

interface TemplateDetail extends TemplateInfo {
  content: string;
}

export default function Templates() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateDetail | null>(null);
  const [title, setTitle] = useState('');
  const [showModal, setShowModal] = useState(false);

  // Fetch templates list
  const { data: templates, isLoading } = useQuery<TemplateInfo[]>({
    queryKey: ['templates'],
    queryFn: () => api.get<TemplateInfo[]>('/api/templates'),
  });

  // Fetch template detail
  const { mutate: fetchDetail } = useMutation<TemplateDetail, Error, string>({
    mutationFn: (id) => api.get<TemplateDetail>(`/api/templates/${id}`),
    onSuccess: (data) => {
      setSelectedTemplate(data);
      setTitle(data.name);
      setShowModal(true);
    },
  });

  // Apply template
  const { mutate: applyTemplate, isPending } = useMutation<{ slug: string }, Error, { template_id: string; title: string; variables: Record<string, string> }>({
    mutationFn: (data) =>
      api.post(`/api/templates/${data.template_id}/apply`, {
        title: data.title,
        variables: data.variables,
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['pages'] });
      setShowModal(false);
      navigate(`/page/${result.slug}`);
    },
  });

  const handleTemplateClick = (templateId: string) => {
    fetchDetail(templateId);
  };

  const handleApply = () => {
    if (!selectedTemplate || !title.trim()) return;

    const variables: Record<string, string> = { title: title.trim() };
    // Add date variable
    if (selectedTemplate.variables.includes('date')) {
      variables.date = new Date().toISOString().split('T')[0];
    }

    applyTemplate({
      template_id: selectedTemplate.id,
      title: title.trim(),
      variables,
    });
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Templates</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-32 bg-gray-200 dark:bg-gray-700 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Templates</h1>
      <p className="text-gray-600 dark:text-gray-400 mb-6">
        Choose a template to quickly create a new page
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates?.map((template) => (
          <button
            key={template.id}
            onClick={() => handleTemplateClick(template.id)}
            className="text-left p-5 bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700
              hover:border-blue-500 dark:hover:border-blue-500 hover:shadow-md transition-all"
          >
            <div className="text-3xl mb-3">{template.icon}</div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
              {template.name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
              {template.description}
            </p>
          </button>
        ))}
      </div>

      {/* Modal */}
      {showModal && selectedTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              {selectedTemplate.icon} {selectedTemplate.name}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {selectedTemplate.description}
            </p>

            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Page Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter page title"
              className="w-full px-3 py-2 border dark:border-gray-600 rounded-lg
                bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white
                focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              autoFocus
            />

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700
                  hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleApply}
                disabled={!title.trim() || isPending}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg
                  disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isPending ? 'Creating...' : 'Create Page'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
