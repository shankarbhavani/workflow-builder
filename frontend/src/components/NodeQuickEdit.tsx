import { useState, useEffect, useRef } from 'react';
import { X, Save, Settings } from 'lucide-react';
import { Node } from 'reactflow';

interface NodeQuickEditProps {
  node: Node;
  onSave: (nodeId: string, config: Record<string, any>) => void;
  onClose: () => void;
  onOpenFullConfig: () => void;
}

export default function NodeQuickEdit({ node, onSave, onClose, onOpenFullConfig }: NodeQuickEditProps) {
  const [config, setConfig] = useState<Record<string, any>>({});
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (node?.data.config) {
      setConfig(node.data.config);
    }
  }, [node]);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (overlayRef.current && !overlayRef.current.contains(e.target as Node)) {
        handleSave(); // Auto-save on blur
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [config]);

  const handleSave = () => {
    onSave(node.id, config);
    onClose();
  };

  const handleFieldChange = (section: string, field: string, value: any) => {
    setConfig({
      ...config,
      [section]: {
        ...config[section],
        [field]: value,
      },
    });
  };

  // Get the 3-5 most important fields to show
  const getQuickEditFields = () => {
    const action = node.data.action;
    if (!action) return [];

    const fields: Array<{ section: string; key: string; def: any }> = [];

    // Event data - always show agent_id and shipper_id
    const eventData = action.parameters?.event_data || {};
    if (eventData.agent_id) {
      fields.push({ section: 'event_data', key: 'agent_id', def: eventData.agent_id });
    }
    if (eventData.shipper_id) {
      fields.push({ section: 'event_data', key: 'shipper_id', def: eventData.shipper_id });
    }

    // Configurations - get required fields first, then first 3 non-required
    const configs = action.parameters?.configurations || {};
    const requiredFields = Object.entries(configs)
      .filter(([_, def]: [string, any]) => def.required)
      .slice(0, 3);

    requiredFields.forEach(([key, def]) => {
      fields.push({ section: 'configurations', key, def });
    });

    // If less than 5 fields, add some optional ones
    if (fields.length < 5) {
      const optionalFields = Object.entries(configs)
        .filter(([_, def]: [string, any]) => !def.required)
        .slice(0, 5 - fields.length);

      optionalFields.forEach(([key, def]) => {
        fields.push({ section: 'configurations', key, def });
      });
    }

    return fields.slice(0, 5); // Max 5 fields
  };

  const quickFields = getQuickEditFields();

  const renderField = (section: string, fieldKey: string, fieldDef: any) => {
    const value = config[section]?.[fieldKey] || '';
    const fieldType = fieldDef.type || 'string';
    const required = fieldDef.required || false;

    if (fieldType === 'boolean') {
      return (
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={value === true}
            onChange={(e) => handleFieldChange(section, fieldKey, e.target.checked)}
            className="w-4 h-4 text-primary focus:ring-primary border-gray-300 rounded"
          />
          <span className="text-sm">{fieldKey}</span>
          {required && <span className="text-red-500 text-xs">*</span>}
        </label>
      );
    }

    if (fieldType === 'number') {
      return (
        <div>
          <label className="text-sm font-medium text-gray-700 mb-1 block">
            {fieldKey}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <input
            type="number"
            value={value}
            onChange={(e) => handleFieldChange(section, fieldKey, parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary text-sm"
            placeholder={fieldDef.default?.toString() || ''}
          />
        </div>
      );
    }

    // Default: text input
    return (
      <div>
        <label className="text-sm font-medium text-gray-700 mb-1 block">
          {fieldKey}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <input
          type="text"
          value={value}
          onChange={(e) => handleFieldChange(section, fieldKey, e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleSave();
            if (e.key === 'Escape') onClose();
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary text-sm"
          placeholder={fieldDef.default || ''}
          autoFocus={fieldKey === quickFields[0]?.key}
        />
        {fieldDef.description && (
          <p className="text-xs text-gray-500 mt-1">{fieldDef.description}</p>
        )}
      </div>
    );
  };

  if (!node || quickFields.length === 0) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
      <div
        ref={overlayRef}
        className="bg-white rounded-lg shadow-2xl w-full max-w-md mx-4 max-h-[90vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <div>
            <h3 className="font-semibold text-gray-900">Quick Edit</h3>
            <p className="text-xs text-gray-600 mt-0.5">{node.data.label}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-200 rounded transition-colors"
            title="Close (Esc)"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Fields */}
        <div className="p-4 space-y-4 max-h-[60vh] overflow-y-auto">
          {quickFields.map(({ section, key, def }) => (
            <div key={`${section}-${key}`}>
              {renderField(section, key, def)}
            </div>
          ))}

          {quickFields.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              No parameters to configure
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t bg-gray-50">
          <button
            onClick={onOpenFullConfig}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-200 rounded transition-colors"
          >
            <Settings className="w-4 h-4" />
            Advanced
          </button>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-primary text-white rounded-md hover:bg-primary-dark"
            >
              <Save className="w-4 h-4" />
              Save
            </button>
          </div>
        </div>

        {/* Keyboard hints */}
        <div className="px-4 py-2 bg-blue-50 border-t border-blue-100">
          <p className="text-xs text-gray-600">
            <span className="font-semibold">Enter</span> to save • <span className="font-semibold">Esc</span> to cancel
          </p>
        </div>
      </div>
    </div>
  );
}
