import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  Action,
  Workflow,
  WorkflowCreateRequest,
  WorkflowUpdateRequest,
  WorkflowExecuteRequest,
  Execution,
  LoginRequest,
  TokenResponse,
  User,
} from '@/types/workflow.types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>('/auth/login', credentials);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  // Action endpoints
  async getActions(params?: { category?: string; search?: string }): Promise<Action[]> {
    const response = await this.client.get<{ actions: Action[] }>('/actions', { params });
    return response.data.actions;
  }

  async getAction(id: string): Promise<Action> {
    const response = await this.client.get<Action>(`/actions/${id}`);
    return response.data;
  }

  // Workflow endpoints
  async getWorkflows(): Promise<Workflow[]> {
    const response = await this.client.get<{ workflows: Workflow[] }>('/workflows');
    return response.data.workflows;
  }

  async getWorkflow(id: string): Promise<Workflow> {
    const response = await this.client.get<Workflow>(`/workflows/${id}`);
    return response.data;
  }

  async createWorkflow(data: WorkflowCreateRequest): Promise<Workflow> {
    const response = await this.client.post<Workflow>('/workflows', data);
    return response.data;
  }

  async updateWorkflow(id: string, data: WorkflowUpdateRequest): Promise<Workflow> {
    const response = await this.client.put<Workflow>(`/workflows/${id}`, data);
    return response.data;
  }

  async deleteWorkflow(id: string): Promise<void> {
    await this.client.delete(`/workflows/${id}`);
  }

  async executeWorkflow(id: string, data: WorkflowExecuteRequest): Promise<Execution> {
    const response = await this.client.post<{ execution: Execution }>(
      `/workflows/${id}/execute`,
      data
    );
    return response.data.execution;
  }

  // Execution endpoints
  async getExecutions(params?: {
    workflow_id?: string;
    status?: string;
  }): Promise<Execution[]> {
    const response = await this.client.get<{ executions: Execution[] }>('/executions', {
      params,
    });
    return response.data.executions;
  }

  async getExecution(id: string): Promise<Execution> {
    const response = await this.client.get<Execution>(`/executions/${id}`);
    return response.data;
  }

  async cancelExecution(id: string): Promise<void> {
    await this.client.post(`/executions/${id}/cancel`);
  }
}

export const api = new ApiClient();
