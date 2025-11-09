import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '@/services/api';
import { Execution, ExecutionStatus } from '@/types/workflow.types';
import { format, formatDistanceToNow } from 'date-fns';

const TEMPORAL_WEB_URL = 'http://localhost:8080';
const TEMPORAL_NAMESPACE = 'default';

export default function ExecutionList() {
  const navigate = useNavigate();
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  useEffect(() => {
    loadExecutions();
    // Auto-refresh every 10 seconds
    const interval = setInterval(loadExecutions, 10000);
    return () => clearInterval(interval);
  }, [selectedStatus]);

  const loadExecutions = async () => {
    try {
      const params = selectedStatus !== 'all' ? { status: selectedStatus } : undefined;
      const data = await api.getExecutions(params);
      setExecutions(data);
    } catch (error: any) {
      console.error('Failed to load executions:', error);
      toast.error('Failed to load executions');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (executionId: string) => {
    if (!confirm('Are you sure you want to cancel this execution?')) {
      return;
    }

    setCancellingId(executionId);
    try {
      await api.cancelExecution(executionId);
      toast.success('Execution cancelled');
      await loadExecutions();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to cancel execution');
    } finally {
      setCancellingId(null);
    }
  };

  const openInTemporal = (execution: Execution) => {
    const url = `${TEMPORAL_WEB_URL}/namespaces/${TEMPORAL_NAMESPACE}/workflows/${execution.temporal_workflow_id}`;
    window.open(url, '_blank');
  };

  const getStatusColor = (status: ExecutionStatus) => {
    switch (status) {
      case 'RUNNING':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'COMPLETED':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'FAILED':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: ExecutionStatus) => {
    switch (status) {
      case 'RUNNING':
        return '🔄';
      case 'COMPLETED':
        return '✅';
      case 'FAILED':
        return '❌';
      case 'CANCELLED':
        return '🚫';
      default:
        return '❓';
    }
  };

  const calculateDuration = (execution: Execution) => {
    const start = new Date(execution.started_at);
    const end = execution.completed_at ? new Date(execution.completed_at) : new Date();
    const durationMs = end.getTime() - start.getTime();

    const seconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const filteredExecutions = executions.filter((execution) =>
    execution.workflow_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const statusCounts = {
    all: executions.length,
    RUNNING: executions.filter((e) => e.status === 'RUNNING').length,
    COMPLETED: executions.filter((e) => e.status === 'COMPLETED').length,
    FAILED: executions.filter((e) => e.status === 'FAILED').length,
    CANCELLED: executions.filter((e) => e.status === 'CANCELLED').length,
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading executions...</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Workflow Executions</h1>
            <p className="text-sm text-gray-500 mt-1">
              Monitor all workflow executions in real-time
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              Manage Workflows
            </button>
            <button
              onClick={() => navigate('/workflows/new')}
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-blue-700"
            >
              Create Workflow
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center gap-4">
          {/* Status Filter */}
          <div className="flex gap-2">
            <button
              onClick={() => setSelectedStatus('all')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                selectedStatus === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({statusCounts.all})
            </button>
            <button
              onClick={() => setSelectedStatus('RUNNING')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                selectedStatus === 'RUNNING'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Running ({statusCounts.RUNNING})
            </button>
            <button
              onClick={() => setSelectedStatus('COMPLETED')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                selectedStatus === 'COMPLETED'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Completed ({statusCounts.COMPLETED})
            </button>
            <button
              onClick={() => setSelectedStatus('FAILED')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                selectedStatus === 'FAILED'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Failed ({statusCounts.FAILED})
            </button>
            <button
              onClick={() => setSelectedStatus('CANCELLED')}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                selectedStatus === 'CANCELLED'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Cancelled ({statusCounts.CANCELLED})
            </button>
          </div>

          {/* Search */}
          <div className="flex-1 max-w-md">
            <input
              type="text"
              placeholder="Search by workflow name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Refresh Button */}
          <button
            onClick={loadExecutions}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 flex items-center gap-2"
          >
            <span>🔄</span>
            Refresh
          </button>
        </div>
      </div>

      {/* Executions List */}
      <div className="flex-1 overflow-y-auto p-6">
        {filteredExecutions.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-gray-400 text-4xl mb-4">📋</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">No Executions Found</h3>
            <p className="text-gray-500">
              {searchQuery
                ? 'No executions match your search criteria'
                : 'No workflow executions yet. Create and execute a workflow to get started!'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredExecutions.map((execution) => (
              <div
                key={execution.id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-5"
              >
                <div className="flex items-start justify-between">
                  {/* Left: Execution Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {execution.workflow_name}
                      </h3>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(
                          execution.status
                        )}`}
                      >
                        {getStatusIcon(execution.status)} {execution.status}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Started:</span>{' '}
                        {format(new Date(execution.started_at), 'MMM d, yyyy HH:mm:ss')}
                        <span className="text-gray-400 ml-2">
                          ({formatDistanceToNow(new Date(execution.started_at), { addSuffix: true })})
                        </span>
                      </div>
                      {execution.completed_at && (
                        <div>
                          <span className="font-medium">Completed:</span>{' '}
                          {format(new Date(execution.completed_at), 'MMM d, yyyy HH:mm:ss')}
                        </div>
                      )}
                      <div>
                        <span className="font-medium">Duration:</span> {calculateDuration(execution)}
                      </div>
                      <div>
                        <span className="font-medium">Execution ID:</span>{' '}
                        <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                          {execution.id.slice(0, 8)}...
                        </code>
                      </div>
                    </div>

                    {execution.error_message && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                        <p className="text-sm text-red-800">
                          <span className="font-semibold">Error:</span> {execution.error_message}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Right: Actions */}
                  <div className="flex flex-col gap-2 ml-6">
                    <button
                      onClick={() => openInTemporal(execution)}
                      className="px-4 py-2 bg-purple-600 text-white rounded text-sm hover:bg-purple-700 whitespace-nowrap"
                    >
                      View in Temporal
                    </button>
                    {execution.status === 'RUNNING' && (
                      <button
                        onClick={() => handleCancel(execution.id)}
                        disabled={cancellingId === execution.id}
                        className="px-4 py-2 bg-red-600 text-white rounded text-sm hover:bg-red-700 disabled:opacity-50 whitespace-nowrap"
                      >
                        {cancellingId === execution.id ? 'Cancelling...' : 'Cancel'}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="bg-white border-t px-6 py-3">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div>
            Showing {filteredExecutions.length} of {executions.length} executions
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-400">Auto-refreshing every 10 seconds</span>
            <span className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></span>
          </div>
        </div>
      </div>
    </div>
  );
}
