import { useState, useRef, useEffect } from 'react';
import { Send, X, MessageSquare, Target } from 'lucide-react';
import { Node } from 'reactflow';
import { chatAPI } from '../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface ChatPanelProps {
  onWorkflowUpdate?: (workflowDraft: any) => void;
  onClose?: () => void;
  showHeader?: boolean;
  selectedNode?: Node | null;
  allNodes?: Node[];
}

export default function ChatPanel({
  onWorkflowUpdate,
  onClose,
  showHeader = true,
  selectedNode,
  allNodes
}: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate context-aware suggestions based on selected node
  const getContextSuggestions = (): string[] => {
    if (!selectedNode) {
      return [
        "Create a workflow to follow up with carriers about late shipments",
        "Build a workflow that processes incoming emails and extracts data",
        "Set up an escalation workflow for loads without responses"
      ];
    }

    const nodeName = selectedNode.data.label || selectedNode.data.action_name;
    return [
      `What does the ${nodeName} action do?`,
      `Configure this ${nodeName} action for me`,
      `What should I connect after ${nodeName}?`,
      `Show me example parameters for ${nodeName}`
    ];
  };

  const contextSuggestions = getContextSuggestions();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (messageText?: string) => {
    const textToSend = messageText || input.trim();
    if (!textToSend || isLoading) return;

    // Build context-enriched message
    let enrichedMessage = textToSend;
    if (selectedNode) {
      const nodeInfo = `\n\n[Context: Currently viewing "${selectedNode.data.label}" (${selectedNode.data.action_name}) node]`;
      enrichedMessage = textToSend + nodeInfo;
    }
    if (allNodes && allNodes.length > 0) {
      enrichedMessage += `\n[Current workflow has ${allNodes.length} nodes]`;
    }

    const userMessage: Message = {
      role: 'user',
      content: textToSend, // Show clean message to user
    };

    // Add user message immediately
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage({
        message: enrichedMessage, // Send enriched message to backend
        session_id: sessionId || undefined,
      });

      // Update session ID if new session
      if (!sessionId) {
        setSessionId(response.session_id);
      }

      // Add assistant response
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Update workflow draft in canvas if provided
      if (response.workflow_draft && onWorkflowUpdate) {
        onWorkflowUpdate(response.workflow_draft);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border-l border-gray-200">
      {/* Header - Optional */}
      {showHeader && (
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-gray-900">Workflow Assistant</h3>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
              aria-label="Close chat"
            >
              <X className="w-5 h-5 text-gray-600" />
            </button>
          )}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Context Indicator */}
        {selectedNode && (
          <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
            <Target className="w-4 h-4 text-blue-600 flex-shrink-0" />
            <div>
              <span className="font-medium text-blue-900">Context:</span>
              <span className="text-blue-700 ml-1">{selectedNode.data.label}</span>
            </div>
          </div>
        )}

        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="text-sm">
              Hi! I'm your workflow assistant. {selectedNode ? 'Ask me about this action or' : 'Describe the workflow you\'d like to create, and I\'ll help you build it.'}
            </p>

            {/* Quick Suggestions */}
            <div className="mt-4 space-y-2 max-w-sm mx-auto">
              <p className="text-xs font-semibold text-gray-700">
                {selectedNode ? '💡 Quick actions:' : '💡 Try asking:'}
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {contextSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSendMessage(suggestion)}
                    className="text-xs px-3 py-1.5 bg-white border border-gray-300 rounded-full hover:bg-gray-50 hover:border-primary transition-colors text-gray-700"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your workflow..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!input.trim() || isLoading}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
