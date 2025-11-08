import { useState, useCallback, useEffect } from 'react';
import { Node, Edge } from 'reactflow';

/**
 * Command pattern for undo/redo functionality
 */
interface WorkflowCommand {
  type: 'ADD_NODE' | 'DELETE_NODE' | 'UPDATE_NODE' | 'ADD_EDGE' | 'DELETE_EDGE' | 'CLEAR_ALL' | 'BATCH';
  timestamp: number;
  description: string;
  execute: () => void;
  undo: () => void;
}

interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
}

export interface UseWorkflowHistoryReturn {
  // State
  canUndo: boolean;
  canRedo: boolean;
  history: Array<{ description: string; timestamp: number }>;

  // Actions
  undo: () => void;
  redo: () => void;
  recordCommand: (command: Omit<WorkflowCommand, 'timestamp'>) => void;
  clearHistory: () => void;
}

const MAX_HISTORY_SIZE = 50;

export function useWorkflowHistory(
  nodes: Node[],
  edges: Edge[],
  setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void,
  setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void
): UseWorkflowHistoryReturn {
  const [undoStack, setUndoStack] = useState<WorkflowCommand[]>([]);
  const [redoStack, setRedoStack] = useState<WorkflowCommand[]>([]);
  const [isExecutingCommand, setIsExecutingCommand] = useState(false);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent undo/redo when typing in inputs
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return;
      }

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const ctrlKey = isMac ? e.metaKey : e.ctrlKey;

      // Undo: Ctrl+Z or Cmd+Z
      if (ctrlKey && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
      }

      // Redo: Ctrl+Y or Cmd+Shift+Z
      if ((ctrlKey && e.key === 'y') || (ctrlKey && e.shiftKey && e.key === 'z')) {
        e.preventDefault();
        redo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [undoStack, redoStack]);

  const recordCommand = useCallback(
    (command: Omit<WorkflowCommand, 'timestamp'>) => {
      if (isExecutingCommand) return;

      const fullCommand: WorkflowCommand = {
        ...command,
        timestamp: Date.now(),
      };

      setUndoStack((prev) => {
        const newStack = [...prev, fullCommand];
        // Limit history size
        if (newStack.length > MAX_HISTORY_SIZE) {
          return newStack.slice(-MAX_HISTORY_SIZE);
        }
        return newStack;
      });

      // Clear redo stack when new command is recorded
      setRedoStack([]);
    },
    [isExecutingCommand]
  );

  const undo = useCallback(() => {
    if (undoStack.length === 0) return;

    const command = undoStack[undoStack.length - 1];
    setIsExecutingCommand(true);

    try {
      command.undo();
      setUndoStack((prev) => prev.slice(0, -1));
      setRedoStack((prev) => [...prev, command]);
    } finally {
      setIsExecutingCommand(false);
    }
  }, [undoStack]);

  const redo = useCallback(() => {
    if (redoStack.length === 0) return;

    const command = redoStack[redoStack.length - 1];
    setIsExecutingCommand(true);

    try {
      command.execute();
      setRedoStack((prev) => prev.slice(0, -1));
      setUndoStack((prev) => [...prev, command]);
    } finally {
      setIsExecutingCommand(false);
    }
  }, [redoStack]);

  const clearHistory = useCallback(() => {
    setUndoStack([]);
    setRedoStack([]);
  }, []);

  const history = undoStack.map((cmd) => ({
    description: cmd.description,
    timestamp: cmd.timestamp,
  }));

  return {
    canUndo: undoStack.length > 0,
    canRedo: redoStack.length > 0,
    history: history.slice(-10), // Last 10 actions
    undo,
    redo,
    recordCommand,
    clearHistory,
  };
}

/**
 * Helper functions to create common commands
 */
export const WorkflowCommands = {
  addNode: (
    node: Node,
    setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void
  ): Omit<WorkflowCommand, 'timestamp'> => ({
    type: 'ADD_NODE',
    description: `Add ${node.data.label || 'node'}`,
    execute: () => setNodes((prev) => [...prev, node]),
    undo: () => setNodes((prev) => prev.filter((n) => n.id !== node.id)),
  }),

  deleteNode: (
    nodeId: string,
    deletedNode: Node,
    setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void,
    setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void,
    deletedEdges: Edge[]
  ): Omit<WorkflowCommand, 'timestamp'> => ({
    type: 'DELETE_NODE',
    description: `Delete ${deletedNode.data.label || 'node'}`,
    execute: () => {
      setNodes((prev) => prev.filter((n) => n.id !== nodeId));
      setEdges((prev) => prev.filter((e) => e.source !== nodeId && e.target !== nodeId));
    },
    undo: () => {
      setNodes((prev) => [...prev, deletedNode]);
      setEdges((prev) => [...prev, ...deletedEdges]);
    },
  }),

  updateNode: (
    nodeId: string,
    oldData: any,
    newData: any,
    setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void
  ): Omit<WorkflowCommand, 'timestamp'> => ({
    type: 'UPDATE_NODE',
    description: `Update node configuration`,
    execute: () => {
      setNodes((prev) =>
        prev.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, ...newData } } : n))
      );
    },
    undo: () => {
      setNodes((prev) =>
        prev.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, ...oldData } } : n))
      );
    },
  }),

  addEdge: (
    edge: Edge,
    setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void
  ): Omit<WorkflowCommand, 'timestamp'> => ({
    type: 'ADD_EDGE',
    description: `Connect nodes`,
    execute: () => setEdges((prev) => [...prev, edge]),
    undo: () => setEdges((prev) => prev.filter((e) => e.id !== edge.id)),
  }),

  deleteEdge: (
    edgeId: string,
    deletedEdge: Edge,
    setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void
  ): Omit<WorkflowCommand, 'timestamp'> => ({
    type: 'DELETE_EDGE',
    description: `Disconnect nodes`,
    execute: () => setEdges((prev) => prev.filter((e) => e.id !== edgeId)),
    undo: () => setEdges((prev) => [...prev, deletedEdge]),
  }),

  clearAll: (
    oldNodes: Node[],
    oldEdges: Edge[],
    setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void,
    setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void
  ): Omit<WorkflowCommand, 'timestamp'> => ({
    type: 'CLEAR_ALL',
    description: `Clear canvas`,
    execute: () => {
      setNodes([]);
      setEdges([]);
    },
    undo: () => {
      setNodes(oldNodes);
      setEdges(oldEdges);
    },
  }),
};
