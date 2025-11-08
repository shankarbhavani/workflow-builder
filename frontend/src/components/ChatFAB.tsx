import { useState } from 'react';
import { MessageSquare, X, Minimize2, Maximize2 } from 'lucide-react';
import { Node } from 'reactflow';
import ChatPanel from './ChatPanel';

interface ChatFABProps {
  onWorkflowUpdate?: (workflowDraft: any) => void;
  selectedNode?: Node | null;
  allNodes?: Node[];
}

export default function ChatFAB({ onWorkflowUpdate, selectedNode, allNodes }: ChatFABProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const handleToggle = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setUnreadCount(0); // Clear unread when opening
      setIsMinimized(false);
    }
  };

  const handleMinimize = () => {
    setIsMinimized(true);
  };

  const handleMaximize = () => {
    setIsMinimized(false);
  };

  const handleClose = () => {
    setIsOpen(false);
    setIsMinimized(false);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          onClick={handleToggle}
          className="relative w-14 h-14 bg-primary text-white rounded-full shadow-lg hover:bg-primary-dark transition-all hover:scale-110 flex items-center justify-center group"
          title="Open Chat Assistant"
        >
          <MessageSquare className="w-6 h-6" />

          {/* Unread Badge */}
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
              {unreadCount}
            </span>
          )}

          {/* Tooltip */}
          <span className="absolute bottom-full mb-2 right-0 px-3 py-1 bg-gray-900 text-white text-sm rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
            Chat Assistant
          </span>
        </button>
      )}

      {/* Chat Panel Container */}
      {isOpen && (
        <div
          className={`bg-white rounded-lg shadow-2xl border border-gray-200 transition-all ${
            isMinimized
              ? 'w-80 h-14'
              : 'w-96 h-[600px]'
          }`}
        >
          {isMinimized ? (
            /* Minimized Header */
            <div className="flex items-center justify-between p-3 border-b border-gray-200 h-full">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-primary" />
                <span className="font-semibold text-gray-900">Workflow Assistant</span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={handleMaximize}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                  title="Maximize"
                >
                  <Maximize2 className="w-4 h-4 text-gray-600" />
                </button>
                <button
                  onClick={handleClose}
                  className="p-1 hover:bg-gray-100 rounded transition-colors"
                  title="Close"
                >
                  <X className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>
          ) : (
            /* Full Chat Panel with Minimize Option */
            <div className="h-full flex flex-col">
              {/* Custom Header with Minimize Button */}
              <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-primary" />
                  <h3 className="font-semibold text-gray-900">Workflow Assistant</h3>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={handleMinimize}
                    className="p-1 hover:bg-gray-100 rounded transition-colors"
                    title="Minimize"
                  >
                    <Minimize2 className="w-4 h-4 text-gray-600" />
                  </button>
                  <button
                    onClick={handleClose}
                    className="p-1 hover:bg-gray-100 rounded transition-colors"
                    title="Close"
                  >
                    <X className="w-4 h-4 text-gray-600" />
                  </button>
                </div>
              </div>

              {/* Chat Panel Content */}
              <div className="flex-1 overflow-hidden">
                <ChatPanel
                  onWorkflowUpdate={onWorkflowUpdate}
                  showHeader={false}
                  selectedNode={selectedNode}
                  allNodes={allNodes}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
