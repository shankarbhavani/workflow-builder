import { useState, useCallback, useMemo, useEffect } from 'react';
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
import { Undo, Redo, History, Sparkles } from 'lucide-react';

import ActionNode from '@/components/ActionNode';
import ActionLibrary from '@/components/ActionLibrary';
import ConfigPanel from '@/components/ConfigPanel';
import ChatFAB from '@/components/ChatFAB';
import NodeQuickEdit from '@/components/NodeQuickEdit';
import { api } from '@/services/api';
import { Action } from '@/types/workflow.types';
import { useWorkflowHistory, WorkflowCommands } from '@/hooks/useWorkflowHistory';

const nodeTypes = {
  action: ActionNode,
};

export default function WorkflowCanvas() {
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState([]);
  const [workflowName, setWorkflowName] = useState('');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [quickEditNode, setQuickEditNode] = useState<Node | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [isGeneratingSuggestion, setIsGeneratingSuggestion] = useState(false);

  // Initialize undo/redo system
  const workflowHistory = useWorkflowHistory(nodes, edges, setNodes, setEdges);

  // Wrap onEdgesChange to track edge deletions for undo/redo
  const onEdgesChange = useCallback(
    (changes: any[]) => {
      // Detect edge removals
      const removedEdges = changes
        .filter((change) => change.type === 'remove')
        .map((change) => edges.find((e) => e.id === change.id))
        .filter(Boolean);

      // Record deletion commands for removed edges
      removedEdges.forEach((edge) => {
        if (edge) {
          workflowHistory.recordCommand(
            WorkflowCommands.deleteEdge(edge.id, edge, setEdges)
          );
        }
      });

      // Apply changes
      onEdgesChangeInternal(changes);
    },
    [edges, onEdgesChangeInternal, workflowHistory]
  );

  // Show toast on undo/redo
  useEffect(() => {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const modifier = isMac ? '⌘' : 'Ctrl';

    // Show hint on first load
    const hasSeenHint = localStorage.getItem('undoRedoHintSeen');
    if (!hasSeenHint) {
      setTimeout(() => {
        toast(`💡 Tip: Use ${modifier}+Z to undo, ${modifier}+Y to redo`, {
          duration: 5000,
          icon: '⌨️',
        });
        localStorage.setItem('undoRedoHintSeen', 'true');
      }, 2000);
    }
  }, []);

  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge = {
        ...params,
        id: `edge-${Date.now()}`,
      } as Edge;

      setEdges((eds) => [...eds, newEdge]);

      // Record command
      workflowHistory.recordCommand(
        WorkflowCommands.addEdge(newEdge, setEdges)
      );
    },
    [setEdges, workflowHistory]
  );

  const handleDuplicateNode = useCallback(
    (nodeId: string) => {
      const nodeToDuplicate = nodes.find((n) => n.id === nodeId);
      if (!nodeToDuplicate) return;

      const newNode: Node = {
        ...nodeToDuplicate,
        id: `node-${Date.now()}`,
        position: {
          x: nodeToDuplicate.position.x + 50,
          y: nodeToDuplicate.position.y + 50,
        },
        selected: false,
      };

      setNodes((nds) => [...nds, newNode]);

      // Record command
      workflowHistory.recordCommand(
        WorkflowCommands.addNode(newNode, setNodes)
      );

      toast.success('Node duplicated');
    },
    [nodes, setNodes, workflowHistory]
  );

  const handleDeleteNode = useCallback(
    (nodeId: string) => {
      const deletedNode = nodes.find((n) => n.id === nodeId);
      if (!deletedNode) return;

      const deletedEdges = edges.filter(
        (e) => e.source === nodeId || e.target === nodeId
      );

      // Record command before deletion
      workflowHistory.recordCommand(
        WorkflowCommands.deleteNode(nodeId, deletedNode, setNodes, setEdges, deletedEdges)
      );

      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));

      if (selectedNode?.id === nodeId) {
        setSelectedNode(null);
      }

      toast.success('Node deleted');
    },
    [nodes, edges, setNodes, setEdges, selectedNode, workflowHistory]
  );

  const onActionSelect = useCallback(
    (action: Action) => {
      console.log('onActionSelect - Received action:', {
        action_name: action.action_name,
        display_name: action.display_name,
        hasParameters: !!action.parameters,
        parametersKeys: action.parameters ? Object.keys(action.parameters) : [],
        actionKeys: Object.keys(action),
      });

      const nodeId = `node-${Date.now()}`;
      const newNode: Node = {
        id: nodeId,
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
          onConfigure: () => {
            const node = nodes.find((n) => n.id === nodeId);
            if (node) setSelectedNode(node);
          },
          onDuplicate: () => handleDuplicateNode(nodeId),
          onDelete: () => handleDeleteNode(nodeId),
        },
      };

      console.log('onActionSelect - Created node:', {
        nodeId: nodeId,
        hasAction: !!newNode.data.action,
        actionInData: newNode.data.action,
      });

      setNodes((nds) => {
        const updatedNodes = [...nds, newNode];
        console.log('onActionSelect - After setNodes, checking last node:', {
          lastNodeHasAction: !!updatedNodes[updatedNodes.length - 1].data.action,
        });
        return updatedNodes;
      });

      // Record command
      workflowHistory.recordCommand(
        WorkflowCommands.addNode(newNode, setNodes)
      );

      toast.success(`Added ${action.display_name}`);
    },
    [setNodes, nodes, handleDuplicateNode, handleDeleteNode, workflowHistory]
  );

  const onNodeClick: NodeMouseHandler = useCallback((event, node) => {
    console.log('onNodeClick - Node data:', {
      id: node.id,
      label: node.data.label,
      action_name: node.data.action_name,
      hasAction: !!node.data.action,
      actionKeys: node.data.action ? Object.keys(node.data.action) : [],
      hasParameters: !!(node.data.action?.parameters),
    });
    setSelectedNode(node);
  }, []);

  const onNodeDoubleClick: NodeMouseHandler = useCallback((event, node) => {
    setQuickEditNode(node);
  }, []);

  const handleConfigChange = useCallback(
    (nodeId: string, config: Record<string, any>) => {
      const oldNode = nodes.find((n) => n.id === nodeId);
      if (!oldNode) return;

      const oldConfig = oldNode.data.config;

      setNodes((nds) =>
        nds.map((node) => {
          if (node.id === nodeId) {
            // Preserve all existing data including action object
            return {
              ...node,
              data: {
                ...node.data,
                config,
                // Explicitly preserve action field
                action: node.data.action,
              },
            };
          }
          return node;
        })
      );

      // Record command
      workflowHistory.recordCommand(
        WorkflowCommands.updateNode(
          nodeId,
          { config: oldConfig },
          { config },
          setNodes
        )
      );

      toast.success('Configuration updated');
    },
    [nodes, setNodes, workflowHistory]
  );

  const handleQuickEditSave = useCallback(
    (nodeId: string, config: Record<string, any>) => {
      handleConfigChange(nodeId, config);
      setQuickEditNode(null);
    },
    [handleConfigChange]
  );

  const handleOpenFullConfig = useCallback(() => {
    if (quickEditNode) {
      setSelectedNode(quickEditNode);
      setQuickEditNode(null);
    }
  }, [quickEditNode]);

  const handleCloseConfig = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const handleWorkflowUpdate = useCallback(
    (workflowDraft: any) => {
      if (workflowDraft && workflowDraft.nodes && workflowDraft.edges) {
        // Preserve action objects from existing nodes when updating from chat
        const updatedNodes = workflowDraft.nodes.map((newNode: Node) => {
          const existingNode = nodes.find((n) => n.id === newNode.id);
          if (existingNode && existingNode.data.action) {
            // Preserve the action object from existing node
            return {
              ...newNode,
              data: {
                ...newNode.data,
                action: existingNode.data.action,
              },
            };
          }
          return newNode;
        });

        setNodes(updatedNodes);
        setEdges(workflowDraft.edges);
        toast.success('Workflow updated from chat');
      }
    },
    [nodes, setNodes, setEdges]
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
    if (nodes.length === 0 && edges.length === 0) {
      toast('Canvas is already empty', { icon: 'ℹ️' });
      return;
    }

    const oldNodes = [...nodes];
    const oldEdges = [...edges];

    setNodes([]);
    setEdges([]);

    // Record command for undo
    workflowHistory.recordCommand(
      WorkflowCommands.clearAll(oldNodes, oldEdges, setNodes, setEdges)
    );

    toast.success('Canvas cleared');
  };

  const handleSuggestMetadata = async () => {
    if (nodes.length === 0) {
      toast.error('Add some actions to the canvas first');
      return;
    }

    setIsGeneratingSuggestion(true);
    try {
      // Call AI suggestion API
      const suggestion = await api.suggestWorkflowMetadata({
        nodes: nodes.map((node) => ({
          id: node.id,
          type: node.type || 'action',
          data: node.data,
          position: node.position,
        })),
        edges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type || 'default',
        })),
      });

      // Update name and description
      setWorkflowName(suggestion.title);
      setWorkflowDescription(suggestion.description);

      toast.success('✨ Suggestions applied!');
    } catch (error: any) {
      console.error('Failed to generate suggestions:', error);
      toast.error('Failed to generate suggestions. Please try again.');
    } finally {
      setIsGeneratingSuggestion(false);
    }
  };

  // Enrich nodes with quick action callbacks
  const enrichedNodes = useMemo(
    () =>
      nodes.map((node) => ({
        ...node,
        data: {
          ...node.data,
          action: node.data.action, // Explicitly preserve action object
          onConfigure: () => {
            // Find the node by ID to get the latest reference
            const currentNode = nodes.find((n) => n.id === node.id);
            console.log('onConfigure clicked:', {
              nodeId: node.id,
              foundNode: !!currentNode,
              hasAction: !!currentNode?.data.action,
              actionName: currentNode?.data.action_name,
              parametersExist: !!(currentNode?.data.action?.parameters),
            });
            if (currentNode) setSelectedNode(currentNode);
          },
          onDuplicate: () => handleDuplicateNode(node.id),
          onDelete: () => handleDeleteNode(node.id),
        },
      })),
    [nodes, handleDuplicateNode, handleDeleteNode]
  );

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex-1 max-w-2xl">
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Workflow name..."
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary text-lg font-semibold"
              />
              <button
                onClick={handleSuggestMetadata}
                disabled={isGeneratingSuggestion || nodes.length === 0}
                className="flex items-center gap-2 px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm font-medium"
                title="AI-powered title & description suggestion"
              >
                {isGeneratingSuggestion ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Suggest</span>
                  </>
                )}
              </button>
            </div>
            <input
              type="text"
              placeholder="Description (optional)..."
              value={workflowDescription}
              onChange={(e) => setWorkflowDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary text-sm mt-2"
            />
          </div>

          <div className="flex gap-2 ml-4">
            {/* Undo/Redo Controls */}
            <div className="flex gap-1 mr-2 border-r border-gray-300 pr-2">
              <button
                onClick={workflowHistory.undo}
                disabled={!workflowHistory.canUndo}
                className="p-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                title={`Undo${workflowHistory.canUndo && workflowHistory.history.length > 0 ? ` (${workflowHistory.history[workflowHistory.history.length - 1]?.description})` : ''}`}
              >
                <Undo className="w-5 h-5" />
              </button>
              <button
                onClick={workflowHistory.redo}
                disabled={!workflowHistory.canRedo}
                className="p-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                title="Redo"
              >
                <Redo className="w-5 h-5" />
              </button>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className={`p-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-all ${showHistory ? 'bg-gray-100' : ''}`}
                title="Show History"
              >
                <History className="w-5 h-5" />
              </button>
            </div>

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

      {/* History Panel */}
      {showHistory && workflowHistory.history.length > 0 && (
        <div className="bg-gray-50 border-b px-6 py-3">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-semibold text-gray-700">Recent Actions</h4>
            <button
              onClick={() => setShowHistory(false)}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              Hide
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {workflowHistory.history.slice().reverse().map((entry, index) => (
              <div
                key={index}
                className="text-xs px-2 py-1 bg-white border border-gray-200 rounded text-gray-600"
              >
                {entry.description}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Action Library Sidebar */}
        <div className="w-80 border-r bg-gray-50">
          <ActionLibrary onActionSelect={onActionSelect} />
        </div>

        {/* Canvas */}
        <div className="flex-1 h-full">
          <ReactFlow
            nodes={enrichedNodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onNodeDoubleClick={onNodeDoubleClick}
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
      </div>

      {/* Floating Chat Assistant */}
      <ChatFAB
        onWorkflowUpdate={handleWorkflowUpdate}
        selectedNode={selectedNode}
        allNodes={nodes}
      />

      {/* Quick Edit Overlay */}
      {quickEditNode && (
        <NodeQuickEdit
          node={quickEditNode}
          onSave={handleQuickEditSave}
          onClose={() => setQuickEditNode(null)}
          onOpenFullConfig={handleOpenFullConfig}
        />
      )}
    </div>
  );
}
