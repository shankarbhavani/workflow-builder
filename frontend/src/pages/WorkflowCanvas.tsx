import { useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  NodeMouseHandler,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { MessageSquare } from 'lucide-react';

import ActionNode from '@/components/ActionNode';
import ActionLibrary from '@/components/ActionLibrary';
import ConfigPanel from '@/components/ConfigPanel';
import ChatPanel from '@/components/ChatPanel';
import { api } from '@/services/api';
import { Action } from '@/types/workflow.types';

const nodeTypes = {
  action: ActionNode,
};

export default function WorkflowCanvas() {
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [showChatPanel, setShowChatPanel] = useState(false);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onActionSelect = useCallback(
    (action: Action) => {
      const newNode: Node = {
        id: `node-${Date.now()}`,
        type: 'action',
        position: {
          x: Math.random() * 400,
          y: Math.random() * 400,
        },
        data: {
          action_name: action.action_name,
          label: action.display_name,
          action: action, // Include full action object
          config: {
            event_data: {},
            configurations: {},
          },
        },
      };
      setNodes((nds) => [...nds, newNode]);
      toast.success(`Added ${action.display_name}`);
    },
    [setNodes]
  );

  const onNodeClick: NodeMouseHandler = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const handleConfigChange = useCallback(
    (nodeId: string, config: Record<string, any>) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === nodeId
            ? { ...node, data: { ...node.data, config } }
            : node
        )
      );
      toast.success('Configuration updated');
    },
    [setNodes]
  );

  const handleCloseConfig = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const handleWorkflowUpdate = useCallback(
    (workflowDraft: any) => {
      if (workflowDraft && workflowDraft.nodes && workflowDraft.edges) {
        setNodes(workflowDraft.nodes);
        setEdges(workflowDraft.edges);
        toast.success('Workflow updated from chat');
      }
    },
    [setNodes, setEdges]
  );

  const handleSave = async () => {
    if (!workflowName.trim()) {
      toast.error('Please enter a workflow name');
      return;
    }

    if (nodes.length === 0) {
      toast.error('Please add at least one action to the workflow');
      return;
    }

    setIsSaving(true);
    try {
      await api.createWorkflow({
        name: workflowName,
        description: workflowDescription,
        config: {
          nodes: nodes as any,
          edges: edges as any,
        },
      });
      toast.success('Workflow saved successfully');
      navigate('/workflows');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save workflow');
    } finally {
      setIsSaving(false);
    }
  };

  const handleClear = () => {
    setNodes([]);
    setEdges([]);
    toast.success('Canvas cleared');
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex-1 max-w-2xl">
            <input
              type="text"
              placeholder="Workflow name..."
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary text-lg font-semibold"
            />
            <input
              type="text"
              placeholder="Description (optional)..."
              value={workflowDescription}
              onChange={(e) => setWorkflowDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary text-sm mt-2"
            />
          </div>

          <div className="flex gap-2 ml-4">
            <button
              onClick={() => setShowChatPanel(!showChatPanel)}
              className={`px-4 py-2 border rounded-md flex items-center gap-2 ${
                showChatPanel
                  ? 'bg-primary text-white border-primary'
                  : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              Chat Assistant
            </button>
            <button
              onClick={handleClear}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Clear
            </button>
            <button
              onClick={() => navigate('/workflows')}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-4 py-2 bg-primary text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Workflow'}
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Action Library Sidebar */}
        <div className="w-80 border-r bg-gray-50">
          <ActionLibrary onActionSelect={onActionSelect} />
        </div>

        {/* Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
          </ReactFlow>
        </div>

        {/* Config Panel */}
        {selectedNode && (
          <ConfigPanel
            selectedNode={selectedNode}
            onConfigChange={handleConfigChange}
            onClose={handleCloseConfig}
          />
        )}

        {/* Chat Panel */}
        {showChatPanel && (
          <div className="w-96">
            <ChatPanel
              onWorkflowUpdate={handleWorkflowUpdate}
              onClose={() => setShowChatPanel(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
