import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { api } from '@/services/api';
import { Workflow, Execution } from '@/types/workflow.types';
import { format } from 'date-fns';

export default function WorkflowList() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [executingId, setExecutingId] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [workflowsData, executionsData] = await Promise.all([
        api.getWorkflows(),
        api.getExecutions(),
      ]);
      setWorkflows(workflowsData);
      setExecutions(executionsData);
    } catch (error: any) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (workflowId: string) => {
    setExecutingId(workflowId);
    try {
      const execution = await api.executeWorkflow(workflowId, { inputs: {} });
      toast.success('Workflow execution started');
      setExecutions([execution, ...executions]);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to execute workflow');
    } finally {
      setExecutingId(null);
    }
  };

  const handleDelete = async (workflowId: string) => {
    if (!confirm('Are you sure you want to delete this workflow?')) {
      return;
    }

    try {
      await api.deleteWorkflow(workflowId);
      toast.success('Workflow deleted');
      setWorkflows(workflows.filter((w) => w.id !== workflowId));
    } catch (error: any) {
      toast.error('Failed to delete workflow');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return 'bg-blue-100 text-blue-800';
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      case 'CANCELLED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
          <button
            onClick={() => navigate('/workflows/new')}
            className="px-4 py-2 bg-primary text-white rounded-md hover:bg-blue-700"
          >
            Create Workflow
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Workflows */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Your Workflows</h2>
            <div className="space-y-3">
              {workflows.length === 0 ? (
                <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                  No workflows yet. Create your first workflow!
                </div>
              ) : (
                workflows.map((workflow) => (
                  <div key={workflow.id} className="bg-white rounded-lg shadow p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{workflow.name}</h3>
                        {workflow.description && (
                          <p className="text-sm text-gray-600 mt-1">
                            {workflow.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                          <span>{workflow.config.nodes.length} actions</span>
                          <span>v{workflow.version}</span>
                          <span>
                            {format(new Date(workflow.created_at), 'MMM d, yyyy')}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => handleExecute(workflow.id)}
                          disabled={executingId === workflow.id}
                          className="px-3 py-1 bg-success text-white rounded text-sm hover:bg-green-600 disabled:opacity-50"
                        >
                          {executingId === workflow.id ? 'Starting...' : 'Execute'}
                        </button>
                        <button
                          onClick={() => handleDelete(workflow.id)}
                          className="px-3 py-1 bg-error text-white rounded text-sm hover:bg-red-600"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Executions */}
          <div>
            <h2 className="text-lg font-semibold mb-4">Recent Executions</h2>
            <div className="space-y-3">
              {executions.length === 0 ? (
                <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                  No executions yet
                </div>
              ) : (
                executions.slice(0, 10).map((execution) => (
                  <div
                    key={execution.id}
                    className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => navigate(`/executions/${execution.id}`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">
                          {execution.workflow_name}
                        </h3>
                        <div className="flex items-center gap-2 mt-2">
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
                              execution.status
                            )}`}
                          >
                            {execution.status}
                          </span>
                          <span className="text-xs text-gray-500">
                            {format(new Date(execution.started_at), 'MMM d, HH:mm')}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
