import { useState, useEffect } from 'react';
import { Node } from 'reactflow';
import { FileText } from 'lucide-react';
import { Action } from '@/types/workflow.types';
import { getTemplatesForAction, ParameterTemplate } from '@/data/parameterTemplates';
import { api } from '@/services/api';

interface ConfigPanelProps {
  selectedNode: Node | null;
  onConfigChange: (nodeId: string, config: Record<string, any>) => void;
  onClose: () => void;
}

export default function ConfigPanel({ selectedNode, onConfigChange, onClose }: ConfigPanelProps) {
  const [config, setConfig] = useState<Record<string, any>>({});
  const [activeTab, setActiveTab] = useState<'event_data' | 'configurations'>('event_data');
  const [availableTemplates, setAvailableTemplates] = useState<ParameterTemplate[]>([]);
  const [action, setAction] = useState<Action | null>(null);
  const [loadingAction, setLoadingAction] = useState(false);

  // Fetch action data by ID when node changes
  useEffect(() => {
    const loadAction = async () => {
      if (!selectedNode?.data.action_id) {
        setAction(null);
        return;
      }

      setLoadingAction(true);
      try {
        const fetchedAction = await api.getAction(selectedNode.data.action_id);
        setAction(fetchedAction);
      } catch (error) {
        console.error('Failed to load action:', error);
        setAction(null);
      } finally {
        setLoadingAction(false);
      }
    };

    loadAction();
  }, [selectedNode?.data.action_id]);

  // Initialize config from node data
  useEffect(() => {
    if (selectedNode?.data.config) {
      setConfig(selectedNode.data.config);
    } else {
      // Initialize with default structure
      setConfig({
        event_data: {
          shipper_id: '',
          agent_id: '',
          parent_request_id: '',
        },
        configurations: {},
      });
    }

    // Load available templates for this action
    if (selectedNode?.data.action_name) {
      const templates = getTemplatesForAction(selectedNode.data.action_name);
      setAvailableTemplates(templates);
    }
  }, [selectedNode]);

  const handleApplyTemplate = (template: ParameterTemplate) => {
    setConfig({
      event_data: { ...config.event_data, ...template.config.event_data },
      configurations: { ...config.configurations, ...template.config.configurations },
    });
  };

  if (!selectedNode) {
    return null;
  }

  if (loadingAction) {
    return (
      <div className="w-96 bg-white border-l flex flex-col h-full">
        <div className="p-4 border-b flex items-center justify-between bg-gray-50">
          <h3 className="font-semibold">Configure Action</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        <div className="p-4 text-gray-500 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (!action) {
    return (
      <div className="w-96 bg-white border-l flex flex-col h-full">
        <div className="p-4 border-b flex items-center justify-between bg-gray-50">
          <h3 className="font-semibold">Configure Action</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        <div className="p-4 text-gray-500">No action data available</div>
      </div>
    );
  }

  const handleFieldChange = (section: string, field: string, value: any) => {
    const updatedConfig = {
      ...config,
      [section]: {
        ...config[section],
        [field]: value,
      },
    };
    setConfig(updatedConfig);
  };

  const handleSave = () => {
    onConfigChange(selectedNode.id, config);
    onClose();
  };

  const handleReset = () => {
    setConfig({
      event_data: {
        shipper_id: '',
        agent_id: '',
        parent_request_id: '',
      },
      configurations: {},
    });
  };

  const renderField = (section: string, fieldName: string, fieldDef: any) => {
    const value = config[section]?.[fieldName] || '';
    const fieldType = fieldDef.type || 'string';
    const required = fieldDef.required || false;
    const description = fieldDef.description || '';

    // Handle different field types
    if (fieldType === 'boolean') {
      return (
        <div key={fieldName} className="mb-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={value === true}
              onChange={(e) => handleFieldChange(section, fieldName, e.target.checked)}
              className="mr-2"
            />
            <span className="text-sm font-medium">
              {fieldName}
              {required && <span className="text-red-500 ml-1">*</span>}
            </span>
          </label>
          {description && <p className="text-xs text-gray-500 mt-1 ml-6">{description}</p>}
        </div>
      );
    }

    if (fieldType === 'number') {
      return (
        <div key={fieldName} className="mb-4">
          <label className="block text-sm font-medium mb-1">
            {fieldName}
            {required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <input
            type="number"
            value={value}
            onChange={(e) => handleFieldChange(section, fieldName, parseFloat(e.target.value) || 0)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary text-sm"
            placeholder={fieldDef.default?.toString() || ''}
          />
          {description && <p className="text-xs text-gray-500 mt-1">{description}</p>}
        </div>
      );
    }

    if (fieldType === 'array' || fieldType === 'object') {
      return (
        <div key={fieldName} className="mb-4">
          <label className="block text-sm font-medium mb-1">
            {fieldName}
            {required && <span className="text-red-500 ml-1">*</span>}
            <span className="text-xs text-gray-500 ml-2">({fieldType})</span>
          </label>
          <textarea
            value={typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleFieldChange(section, fieldName, parsed);
              } catch {
                // Keep as string until valid JSON
                handleFieldChange(section, fieldName, e.target.value);
              }
            }}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary text-sm font-mono"
            placeholder={fieldType === 'array' ? '[]' : '{}'}
          />
          {description && <p className="text-xs text-gray-500 mt-1">{description}</p>}
        </div>
      );
    }

    // Default: string input
    return (
      <div key={fieldName} className="mb-4">
        <label className="block text-sm font-medium mb-1">
          {fieldName}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
        <input
          type="text"
          value={value}
          onChange={(e) => handleFieldChange(section, fieldName, e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary focus:border-primary text-sm"
          placeholder={fieldDef.default || ''}
        />
        {description && <p className="text-xs text-gray-500 mt-1">{description}</p>}
      </div>
    );
  };

  const eventDataParams = action.parameters?.event_data || {};
  const configurationsParams = action.parameters?.configurations || {};

  return (
    <div className="w-96 bg-white border-l flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold">Configure Action</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl leading-none"
          >
            ✕
          </button>
        </div>
        <div className="text-sm text-gray-600">{action.display_name}</div>
        <div className="text-xs text-gray-500 mt-1">{action.domain}</div>
      </div>

      {/* Action Info */}
      <div className="p-4 border-b bg-blue-50">
        <div className="text-xs text-gray-700">{action.description}</div>
      </div>

      {/* Template Selector */}
      {availableTemplates.length > 0 && (
        <div className="p-4 border-b bg-purple-50">
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <FileText className="w-4 h-4 text-purple-600" />
            Load Template
          </label>
          <select
            onChange={(e) => {
              const template = availableTemplates.find((t) => t.name === e.target.value);
              if (template) handleApplyTemplate(template);
            }}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary text-sm"
            defaultValue=""
          >
            <option value="" disabled>
              Select a template...
            </option>
            {availableTemplates.map((template) => (
              <option key={template.name} value={template.name}>
                {template.name}
              </option>
            ))}
          </select>
          {availableTemplates.find((t) => t.name)?.description && (
            <p className="text-xs text-gray-600 mt-1">
              💡 {availableTemplates[0].description}
            </p>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b">
        <button
          onClick={() => setActiveTab('event_data')}
          className={`flex-1 px-4 py-2 text-sm font-medium ${
            activeTab === 'event_data'
              ? 'border-b-2 border-primary text-primary'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Event Data
        </button>
        <button
          onClick={() => setActiveTab('configurations')}
          className={`flex-1 px-4 py-2 text-sm font-medium ${
            activeTab === 'configurations'
              ? 'border-b-2 border-primary text-primary'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Configurations
        </button>
      </div>

      {/* Form Fields */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'event_data' && (
          <div>
            <p className="text-xs text-gray-600 mb-4">
              Common fields required by all actions
            </p>
            {Object.entries(eventDataParams).map(([fieldName, fieldDef]: [string, any]) =>
              renderField('event_data', fieldName, fieldDef)
            )}
          </div>
        )}

        {activeTab === 'configurations' && (
          <div>
            <p className="text-xs text-gray-600 mb-4">
              Action-specific configuration parameters
            </p>
            {Object.keys(configurationsParams).length === 0 ? (
              <div className="text-sm text-gray-500 text-center py-8">
                No configuration parameters for this action
              </div>
            ) : (
              Object.entries(configurationsParams).map(([fieldName, fieldDef]: [string, any]) =>
                renderField('configurations', fieldName, fieldDef)
              )
            )}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t bg-gray-50 flex gap-2">
        <button
          onClick={handleReset}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 text-sm"
        >
          Reset
        </button>
        <button
          onClick={handleSave}
          className="flex-1 px-4 py-2 bg-primary text-white rounded-md hover:bg-blue-700 text-sm"
        >
          Save
        </button>
      </div>
    </div>
  );
}
