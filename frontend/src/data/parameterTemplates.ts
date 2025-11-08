/**
 * Parameter templates for common action configurations
 * Organized by action_name
 */

export interface ParameterTemplate {
  name: string;
  description: string;
  config: {
    event_data?: Record<string, any>;
    configurations?: Record<string, any>;
  };
}

export const parameterTemplates: Record<string, ParameterTemplate[]> = {
  // Load Search Trigger Templates
  'load_search_trigger': [
    {
      name: 'Standard Carrier Follow-up',
      description: 'Search for late loads for daily carrier follow-up',
      config: {
        event_data: {
          agent_id: 'TRACY',
          shipper_id: 'shipper-123',
        },
        configurations: {
          status: 'IN_TRANSIT',
          include_scac_grouped: true,
          enable_webhook_calls: false,
        },
      },
    },
    {
      name: 'Urgent Escalation Search',
      description: 'Find loads requiring urgent escalation',
      config: {
        event_data: {
          agent_id: 'SAM',
          shipper_id: 'shipper-123',
        },
        configurations: {
          status: 'DELAYED',
          include_scac_grouped: false,
          enable_webhook_calls: true,
        },
      },
    },
  ],

  // Send Email Templates
  'send_email': [
    {
      name: 'LLM-Generated Email',
      description: 'Use AI to generate carrier follow-up emails',
      config: {
        event_data: {
          agent_id: 'TRACY',
          shipper_id: 'shipper-123',
        },
        configurations: {
          use_llm_generation: true,
          email_description: 'Friendly carrier follow-up for shipment status',
          is_smart_action: true,
        },
      },
    },
    {
      name: 'Template-Based Email',
      description: 'Use predefined HTML template for emails',
      config: {
        event_data: {
          agent_id: 'TRACY',
          shipper_id: 'shipper-123',
        },
        configurations: {
          use_llm_generation: false,
          email_template: 'Dear {{carrier_name}},\n\nWe are following up on shipment {{load_number}}...',
          is_smart_action: true,
        },
      },
    },
  ],

  // Process Emails Templates
  'process_emails': [
    {
      name: 'Safe Testing Mode',
      description: 'Process emails without triggering webhooks (for testing)',
      config: {
        event_data: {
          agent_id: 'TRACY',
          shipper_id: 'shipper-123',
        },
        configurations: {
          enable_webhook_calls: false,
          enable_redis_state: true,
        },
      },
    },
    {
      name: 'Production Mode',
      description: 'Full processing with webhook routing enabled',
      config: {
        event_data: {
          agent_id: 'TRACY',
          shipper_id: 'shipper-123',
        },
        configurations: {
          enable_webhook_calls: true,
          enable_redis_state: true,
        },
      },
    },
  ],

  // Extract Data Templates
  'extract_data': [
    {
      name: 'Basic Load Extraction',
      description: 'Extract load number, tracking, and dates',
      config: {
        event_data: {
          agent_id: 'TRACY',
          shipper_id: 'shipper-123',
        },
        configurations: {
          source_type: 'email',
          entity_type: 'loads',
          prompts: ['load_number', 'tracking_id', 'pickup_date', 'delivery_date'],
        },
      },
    },
    {
      name: 'Comprehensive Extraction',
      description: 'Extract all available shipment details',
      config: {
        event_data: {
          agent_id: 'TRACY',
          shipper_id: 'shipper-123',
        },
        configurations: {
          source_type: 'email',
          entity_type: 'loads',
          prompts: ['load_number', 'tracking_id', 'pickup_date', 'delivery_date', 'driver_name', 'driver_phone', 'carrier_name'],
        },
      },
    },
  ],

  // Load Update Templates
  'load_update': [
    {
      name: 'Standard Update',
      description: 'Update basic load information',
      config: {
        event_data: {
          agent_id: 'TRACY',
          shipper_id: 'shipper-123',
        },
        configurations: {
          exact_match: false,
        },
      },
    },
    {
      name: 'Exact Match Update',
      description: 'Update specific loads with exact load numbers',
      config: {
        event_data: {
          agent_id: 'TRACY',
          shipper_id: 'shipper-123',
        },
        configurations: {
          exact_match: true,
        },
      },
    },
  ],

  // Get Escalation Milestones Templates
  'get_escalation_milestones': [
    {
      name: 'L1 Escalation',
      description: 'Find loads needing Level 1 escalation',
      config: {
        event_data: {
          agent_id: 'SAM',
          shipper_id: 'shipper-123',
        },
        configurations: {
          escalation_level: 'L1',
        },
      },
    },
    {
      name: 'L2 Escalation',
      description: 'Find loads needing Level 2 escalation',
      config: {
        event_data: {
          agent_id: 'SAM',
          shipper_id: 'shipper-123',
        },
        configurations: {
          escalation_level: 'L2',
        },
      },
    },
    {
      name: 'L3 Escalation',
      description: 'Find loads needing Level 3 escalation',
      config: {
        event_data: {
          agent_id: 'SAM',
          shipper_id: 'shipper-123',
        },
        configurations: {
          escalation_level: 'L3',
        },
      },
    },
  ],
};

/**
 * Get templates for a specific action
 */
export function getTemplatesForAction(actionName: string): ParameterTemplate[] {
  return parameterTemplates[actionName] || [];
}

/**
 * Get all template names across all actions
 */
export function getAllTemplateNames(): string[] {
  const names: string[] = [];
  Object.values(parameterTemplates).forEach((templates) => {
    templates.forEach((template) => names.push(template.name));
  });
  return names;
}
