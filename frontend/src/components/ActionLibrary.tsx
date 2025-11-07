import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Action } from '@/types/workflow.types';

interface ActionLibraryProps {
  onActionSelect?: (action: Action) => void;
}

export default function ActionLibrary({ onActionSelect }: ActionLibraryProps) {
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<string>('all');

  useEffect(() => {
    loadActions();
  }, []);

  const loadActions = async () => {
    try {
      setLoading(true);
      const data = await api.getActions();
      setActions(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load actions');
    } finally {
      setLoading(false);
    }
  };

  const domains = ['all', ...Array.from(new Set(actions.map((a) => a.domain)))];

  const filteredActions = actions.filter((action) => {
    const matchesSearch =
      searchTerm === '' ||
      action.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      action.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesDomain = selectedDomain === 'all' || action.domain === selectedDomain;
    return matchesSearch && matchesDomain;
  });

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-gray-500">Loading actions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b bg-white">
        <h2 className="text-lg font-semibold mb-4">Action Library</h2>

        <input
          type="text"
          placeholder="Search actions..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary mb-3"
        />

        <select
          value={selectedDomain}
          onChange={(e) => setSelectedDomain(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary"
        >
          {domains.map((domain) => (
            <option key={domain} value={domain}>
              {domain === 'all' ? 'All Domains' : domain}
            </option>
          ))}
        </select>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {filteredActions.map((action) => (
          <div
            key={action.id}
            className="p-3 border border-gray-200 rounded-lg hover:border-primary hover:shadow-sm transition-all cursor-pointer bg-white"
            onClick={() => onActionSelect?.(action)}
          >
            <div className="font-medium text-gray-900">{action.display_name}</div>
            <div className="text-xs text-gray-500 mt-1">{action.domain}</div>
            <div className="text-sm text-gray-600 mt-2 line-clamp-2">
              {action.description}
            </div>
          </div>
        ))}

        {filteredActions.length === 0 && (
          <div className="text-center text-gray-500 py-8">No actions found</div>
        )}
      </div>
    </div>
  );
}
