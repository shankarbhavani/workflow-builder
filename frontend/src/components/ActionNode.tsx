import { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Settings, Copy, Trash2, CheckCircle, AlertCircle, Loader } from 'lucide-react';

interface ActionNodeData {
  action_name: string;
  label: string;
  config: Record<string, any>;
  action?: any;
  status?: 'idle' | 'configured' | 'running' | 'error';
  onConfigure?: () => void;
  onDuplicate?: () => void;
  onDelete?: () => void;
}

// Domain color mapping
const domainColors: Record<string, { border: string; bg: string; text: string; accent: string }> = {
  'Carrier Follow Up': { border: 'border-blue-400', bg: 'bg-blue-50', text: 'text-blue-700', accent: 'bg-blue-500' },
  'Shipment Update': { border: 'border-green-400', bg: 'bg-green-50', text: 'text-green-700', accent: 'bg-green-500' },
  'Escalation': { border: 'border-orange-400', bg: 'bg-orange-50', text: 'text-orange-700', accent: 'bg-orange-500' },
  'default': { border: 'border-gray-400', bg: 'bg-gray-50', text: 'text-gray-700', accent: 'bg-gray-500' },
};

function ActionNode({ data, selected, id }: NodeProps<ActionNodeData>) {
  const [isHovered, setIsHovered] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const hasConfig = data.config && (
    Object.keys(data.config.event_data || {}).some(key => data.config.event_data[key]) ||
    Object.keys(data.config.configurations || {}).some(key => data.config.configurations[key])
  );

  // Determine node status
  const status = data.status || (hasConfig ? 'configured' : 'idle');

  // Get domain-based colors
  const domain = data.action?.domain || 'default';
  const colors = domainColors[domain] || domainColors.default;

  // Get status icon
  const StatusIcon = status === 'configured' ? CheckCircle :
                      status === 'running' ? Loader :
                      status === 'error' ? AlertCircle : null;

  // Get key parameters for preview
  const getParamPreview = () => {
    const eventData = data.config?.event_data || {};
    const configs = data.config?.configurations || {};
    const preview: string[] = [];

    if (eventData.agent_id) preview.push(`Agent: ${eventData.agent_id}`);
    if (configs.use_llm_generation) preview.push('LLM: On');
    if (configs.exact_match) preview.push('Exact Match');

    return preview.slice(0, 2); // Max 2 items
  };

  const paramPreview = getParamPreview();

  const handleQuickAction = (e: React.MouseEvent, action: 'configure' | 'duplicate' | 'delete') => {
    e.stopPropagation(); // Prevent node selection

    switch (action) {
      case 'configure':
        data.onConfigure?.();
        break;
      case 'duplicate':
        data.onDuplicate?.();
        break;
      case 'delete':
        data.onDelete?.();
        break;
    }
  };

  return (
    <div
      className={`relative px-4 py-3 shadow-md rounded-lg border-2 min-w-[200px] max-w-[250px] transition-all ${colors.bg} ${
        selected ? `${colors.border} shadow-lg ring-2 ring-opacity-50` : colors.border
      } ${isHovered ? 'shadow-xl' : ''}`}
      onMouseEnter={() => {
        setIsHovered(true);
        setShowTooltip(true);
      }}
      onMouseLeave={() => {
        setIsHovered(false);
        setShowTooltip(false);
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className={`w-3 h-3 !${colors.accent}`}
      />

      {/* Tooltip */}
      {showTooltip && data.action?.description && (
        <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 px-3 py-2 bg-gray-900 text-white text-xs rounded shadow-lg z-20 w-64 pointer-events-none">
          <div className="font-semibold mb-1">{data.label}</div>
          <div className="text-gray-300">{data.action.description}</div>
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-4 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      )}

      {/* Quick Actions Menu */}
      {isHovered && (
        <div className="absolute -top-10 right-0 flex gap-1 bg-white rounded-lg shadow-lg border border-gray-200 p-1 z-10">
          <button
            onClick={(e) => handleQuickAction(e, 'configure')}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors"
            title="Configure"
          >
            <Settings className="w-4 h-4 text-gray-600" />
          </button>
          <button
            onClick={(e) => handleQuickAction(e, 'duplicate')}
            className="p-1.5 hover:bg-gray-100 rounded transition-colors"
            title="Duplicate"
          >
            <Copy className="w-4 h-4 text-gray-600" />
          </button>
          <button
            onClick={(e) => handleQuickAction(e, 'delete')}
            className="p-1.5 hover:bg-red-50 rounded transition-colors"
            title="Delete"
          >
            <Trash2 className="w-4 h-4 text-red-600" />
          </button>
        </div>
      )}

      <div className="flex flex-col">
        {/* Header with Domain & Status */}
        <div className="flex items-center justify-between mb-1">
          <div className={`text-xs uppercase tracking-wide font-medium ${colors.text}`}>
            {domain}
          </div>
          {StatusIcon && (
            <StatusIcon
              className={`w-4 h-4 ${
                status === 'configured' ? 'text-green-500' :
                status === 'running' ? 'text-blue-500 animate-spin' :
                status === 'error' ? 'text-red-500' : 'text-gray-400'
              }`}
              title={status.charAt(0).toUpperCase() + status.slice(1)}
            />
          )}
        </div>

        {/* Node Label */}
        <div className="text-sm font-semibold text-gray-900 mb-1">{data.label}</div>

        {/* Action Name */}
        <div className="text-xs text-gray-600 mb-2">{data.action_name}</div>

        {/* Parameter Preview */}
        {paramPreview.length > 0 && (
          <div className="border-t border-gray-200 pt-2 mt-1">
            {paramPreview.map((param, index) => (
              <div key={index} className="text-xs text-gray-500 flex items-center gap-1">
                <div className={`w-1 h-1 ${colors.accent} rounded-full`}></div>
                <span>{param}</span>
              </div>
            ))}
          </div>
        )}

        {/* Selection Hint */}
        {selected && (
          <div className={`text-xs mt-2 ${colors.text} font-medium`}>
            Click ⚙️ to configure →
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className={`w-3 h-3 !${colors.accent}`}
      />
    </div>
  );
}

export default memo(ActionNode);
