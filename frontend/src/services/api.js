import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
// Supabase token is read via auth store

// Create axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Create a separate axios instance for refresh token requests (no interceptors)
const refreshApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Create a separate axios instance for password reset (no /api/v1 prefix)
const passwordResetApi = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:8000',
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
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
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

// API methods
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  getProfile: () => api.get('/auth/me'),
  refreshToken: () => refreshApi.post('/auth/refresh', {}),
}

export const passwordResetAPI = {
  requestReset: (email) => passwordResetApi.post('/password-reset/request', { email }),
  verifyCode: (email, verification_code) => passwordResetApi.post('/password-reset/verify', { email, verification_code }),
  confirmReset: (email, verification_code, new_password, confirm_password) => 
    passwordResetApi.post('/password-reset/confirm', { email, verification_code, new_password, confirm_password }),
}

export const workflowAPI = {
  // Main workflow endpoints
  getAll: (params) => api.get('/workflows', { params }),
  getWorkflow: (id) => api.get(`/workflows/${id}`),
  create: (data) => api.post('/workflows', data),
  saveWorkflow: (id, data) => api.put(`/workflows/${id}/bulk`, data),
  update: (id, data) => api.put(`/workflows/${id}`, data),
  delete: (id) => api.delete(`/workflows/${id}`),
  
  // Execution endpoints
  execute: (id, data) => api.post(`/workflows/${id}/execute`, data),
  testWorkflow: (id, data) => api.post(`/workflows/${id}/test`, data),
  validate: (id, data) => api.post(`/workflows/${id}/validate`, data),
  
  // Individual node/connection endpoints (for granular operations)
  getNodes: (workflowId) => api.get(`/workflows/${workflowId}/nodes`),
  createNode: (workflowId, data) => api.post(`/workflows/${workflowId}/nodes`, data),
  updateNode: (workflowId, nodeId, data) => api.put(`/workflows/${workflowId}/nodes/${nodeId}`, data),
  deleteNode: (workflowId, nodeId) => api.delete(`/workflows/${workflowId}/nodes/${nodeId}`),
  
  getConnections: (workflowId) => api.get(`/workflows/${workflowId}/connections`),
  createConnection: (workflowId, data) => api.post(`/workflows/${workflowId}/connections`, data),
  updateConnection: (workflowId, connectionId, data) => api.put(`/workflows/${workflowId}/connections/${connectionId}`, data),
  deleteConnection: (workflowId, connectionId) => api.delete(`/workflows/${workflowId}/connections/${connectionId}`),
}

export const workflowsAPI = workflowAPI // Alias for backward compatibility

export const integrationsAPI = {
  getAll: () => api.get('/integrations'),
  getById: (id) => api.get(`/integrations/${id}`),
  create: (data) => api.post('/integrations', data),
  update: (id, data) => api.put(`/integrations/${id}`, data),
  delete: (id) => api.delete(`/integrations/${id}`),
  test: (id) => api.post(`/integrations/${id}/test`),
}

export const executionsAPI = {
  getAll: (params) => api.get('/executions', { params }),
  getById: (id) => api.get(`/executions/${id}`),
  getLogs: (id) => api.get(`/executions/${id}/logs`),
  delete: (id) => api.delete(`/executions/${id}`),
}

export const oauthAPI = {
  getGoogleAuthUrl: (integrationId) => api.get(`/oauth/google/auth-url?integration_id=${integrationId}`),
  getSlackAuthUrl: (integrationId) => api.get(`/oauth/slack/auth-url?integration_id=${integrationId}`),
  revokeToken: (tokenId) => api.delete(`/oauth/tokens/${tokenId}`),
}

export default api 