import axios, { AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { supabase } from '@/lib/supabaseClient'
import { Workflow, WFNode, WFEdge, ExecutionResult } from '@/types/workflow'

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Create a separate axios instance for refresh token requests (no interceptors)
const refreshApi = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Create a separate axios instance for password reset (no /api/v1 prefix)
const passwordResetApi = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    // Prefer Supabase access token if present
    if (authStore.token) config.headers.Authorization = `Bearer ${authStore.token}`
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors and token refresh
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config
    const authStore = useAuthStore()

    // Handle 401 errors (unauthorized) but skip refresh token requests to prevent infinite loops
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url?.includes('/auth/refresh')) {
      originalRequest._retry = true

      try {
        // Try to refresh token using the separate instance
        await authStore.refreshToken()
        
        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${authStore.token}`
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed, logout user
        await authStore.logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

// API interfaces
interface WorkflowBulkUpdate {
  id: string
  name: string
  nodes: WFNode[]
  edges: WFEdge[]
  viewport?: { x: number; y: number; zoom: number }
}

interface WorkflowExecutionRequest {
  test_mode?: boolean
  trigger_data?: any
}

// API methods
export const authAPI = {
  login: (credentials: { email: string; password: string }) => 
    api.post('/auth/login', credentials),
  register: (userData: { email: string; password: string; confirm_password: string; full_name?: string }) => 
    api.post('/auth/register', userData),
  getProfile: () => api.get('/auth/me'),
  refreshToken: () => {
    // Rely on httpOnly cookie set by server
    return refreshApi.post('/auth/refresh', {})
  },
  logout: () => api.post('/auth/logout'),
}

export const passwordResetAPI = {
  requestReset: (email: string) => passwordResetApi.post('/password-reset/request', { email }),
  verifyCode: (email: string, verification_code: string) => passwordResetApi.post('/password-reset/verify', { email, verification_code }),
  confirmReset: (email: string, verification_code: string, new_password: string, confirm_password: string) => 
    passwordResetApi.post('/password-reset/confirm', { email, verification_code, new_password, confirm_password }),
}

export const workflowAPI = {
  // Main workflow endpoints
  getAll: (params?: any): Promise<AxiosResponse<Workflow[]>> => 
    api.get('/workflows', { params }),
  
  getWorkflow: (id: string): Promise<AxiosResponse<Workflow>> => 
    api.get(`/workflows/${id}`),
  
  create: (data: Partial<Workflow>): Promise<AxiosResponse<Workflow>> => 
    api.post('/workflows', data),
  
  saveWorkflow: (id: string, data: WorkflowBulkUpdate): Promise<AxiosResponse<Workflow>> => 
    api.put(`/workflows/${id}/bulk`, data),
  
  update: (id: string, data: Partial<Workflow>): Promise<AxiosResponse<Workflow>> => 
    api.put(`/workflows/${id}`, data),
  
  delete: (id: string): Promise<AxiosResponse<{ message: string }>> => 
    api.delete(`/workflows/${id}`),
  
  // Execution endpoints
  execute: (id: string, data: WorkflowExecutionRequest): Promise<AxiosResponse<{ task_id: string; status: string; message: string }>> => 
    api.post(`/workflows/${id}/execute`, data),
  
  testWorkflow: (id: string, data: WorkflowExecutionRequest): Promise<AxiosResponse<ExecutionResult>> => 
    api.post(`/workflows/${id}/test`, data),
  
  validate: (id: string, data: WorkflowBulkUpdate): Promise<AxiosResponse<{ valid: boolean; errors: string[] }>> => 
    api.post(`/workflows/${id}/validate`, data),
  
  // Individual node/connection endpoints (for granular operations)
  getNodes: (workflowId: string): Promise<AxiosResponse<WFNode[]>> => 
    api.get(`/workflows/${workflowId}/nodes`),
  
  createNode: (workflowId: string, data: Partial<WFNode>): Promise<AxiosResponse<WFNode>> => 
    api.post(`/workflows/${workflowId}/nodes`, data),
  
  updateNode: (workflowId: string, nodeId: string, data: Partial<WFNode>): Promise<AxiosResponse<WFNode>> => 
    api.put(`/workflows/${workflowId}/nodes/${nodeId}`, data),
  
  deleteNode: (workflowId: string, nodeId: string): Promise<AxiosResponse<{ message: string }>> => 
    api.delete(`/workflows/${workflowId}/nodes/${nodeId}`),
  
  getConnections: (workflowId: string): Promise<AxiosResponse<WFEdge[]>> => 
    api.get(`/workflows/${workflowId}/connections`),
  
  createConnection: (workflowId: string, data: Partial<WFEdge>): Promise<AxiosResponse<WFEdge>> => 
    api.post(`/workflows/${workflowId}/connections`, data),
  
  updateConnection: (workflowId: string, connectionId: string, data: Partial<WFEdge>): Promise<AxiosResponse<WFEdge>> => 
    api.put(`/workflows/${workflowId}/connections/${connectionId}`, data),
  
  deleteConnection: (workflowId: string, connectionId: string): Promise<AxiosResponse<{ message: string }>> => 
    api.delete(`/workflows/${workflowId}/connections/${connectionId}`),
}

export const workflowsAPI = workflowAPI // Alias for backward compatibility

export const integrationsAPI = {
  getAll: () => api.get('/integrations'),
  getById: (id: string) => api.get(`/integrations/${id}`),
  create: (data: any) => api.post('/integrations', data),
  update: (id: string, data: any) => api.put(`/integrations/${id}`, data),
  delete: (id: string) => api.delete(`/integrations/${id}`),
  test: (id: string) => api.post(`/integrations/${id}/test`),
}

export const executionsAPI = {
  getAll: (params?: any) => api.get('/executions', { params }),
  getById: (id: string) => api.get(`/executions/${id}`),
  getLogs: (id: string) => api.get(`/executions/${id}/logs`),
  delete: (id: string) => api.delete(`/executions/${id}`),
}

export const oauthAPI = {
  getGoogleAuthUrl: (integrationId: string) => api.get(`/oauth/google/auth-url?integration_id=${integrationId}`),
  getSlackAuthUrl: (integrationId: string) => api.get(`/oauth/slack/auth-url?integration_id=${integrationId}`),
  revokeToken: (tokenId: string) => api.delete(`/oauth/tokens/${tokenId}`),
}

export default api
