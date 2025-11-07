import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface ActionNodeData {
  action_name: string;
  label: string;
  config: Record<string, any>;
}

function ActionNode({ data, selected }: NodeProps<ActionNodeData>) {
  const hasConfig = data.config && (
    Object.keys(data.config.event_data || {}).some(key => data.config.event_data[key]) ||
    Object.keys(data.config.configurations || {}).some(key => data.config.configurations[key])
  );

  return (
    <div
      className={`px-4 py-3 shadow-md rounded-lg bg-white border-2 min-w-[200px] transition-all ${
        selected ? 'border-primary shadow-lg ring-2 ring-primary ring-opacity-50' : 'border-gray-300'
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-primary"
      />

      <div className="flex flex-col">
        <div className="flex items-center justify-between mb-1">
          <div className="text-xs text-gray-500 uppercase tracking-wide">
            Action
          </div>
          {hasConfig && (
            <div className="w-2 h-2 bg-green-500 rounded-full" title="Configured" />
          )}
        </div>
        <div className="text-sm font-semibold text-gray-900">{data.label}</div>
        <div className="text-xs text-gray-600 mt-1">{data.action_name}</div>
        {selected && (
          <div className="text-xs text-primary mt-2">
            Click to configure →
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-primary"
      />
    </div>
  );
}

export default memo(ActionNode);
