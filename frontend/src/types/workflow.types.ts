// Action types
export interface Action {
  id: string;
  action_name: string;
  display_name: string;
  description: string;
  domain: string;
  parameters: Record<string, any>;
  returns: Record<string, any>;
  api_details: {
    endpoint: string;
    http_method: string;
    timeout: number;
  };
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Parameter field definition
export interface ParameterField {
  type: string;
  required: boolean;
  description: string;
  default?: any;
  fields?: Record<string, ParameterField>; // For nested objects
}

// Workflow node types
export interface WorkflowNode {
  id: string;
  type: 'action';
  data: {
    action_name: string;
    label: string;
    action?: Action; // Full action object with parameters
    config: Record<string, any>;
  };
  position: {
    x: number;
    y: number;
  };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
}

export interface WorkflowConfig {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

// Workflow types
export interface Workflow {
  id: string;
  name: string;
  description: string;
  config: WorkflowConfig;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface WorkflowCreateRequest {
  name: string;
  description: string;
  config: WorkflowConfig;
}

export interface WorkflowUpdateRequest {
  name?: string;
  description?: string;
  config?: WorkflowConfig;
  is_active?: boolean;
}

// Execution types
export type ExecutionStatus = 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface ExecutionLog {
  id: string;
  execution_id: string;
  node_id: string;
  action_name: string;
  status: string;
  inputs: Record<string, any>;
  outputs: Record<string, any>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface Execution {
  id: string;
  workflow_id: string;
  workflow_name: string;
  temporal_workflow_id: string;
  status: ExecutionStatus;
  inputs: Record<string, any>;
  outputs?: Record<string, any>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  logs?: ExecutionLog[];
}

export interface WorkflowExecuteRequest {
  inputs: Record<string, any>;
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  username: string;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
