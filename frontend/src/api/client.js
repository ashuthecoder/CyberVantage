import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// API functions
export const auth = {
  register: (data) => apiClient.post('/auth/register', data),
  login: (data) => apiClient.post('/auth/login/json', data),
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  getCurrentUser: () => apiClient.get('/auth/me'),
  requestPasswordReset: (email) => apiClient.post('/auth/password-reset-request', { email }),
  resetPassword: (token, new_password) => apiClient.post('/auth/password-reset', { token, new_password }),
};

export const simulation = {
  getEmails: () => apiClient.get('/simulation/emails'),
  submitResponse: (data) => apiClient.post('/simulation/responses', data),
  getSessions: () => apiClient.get('/simulation/sessions'),
  createSession: (session_id) => apiClient.post('/simulation/sessions', { session_id }),
};

export const analysis = {
  getPerformance: () => apiClient.get('/analysis/performance'),
  getHistory: () => apiClient.get('/analysis/history'),
};

export const threats = {
  checkUrl: (url) => apiClient.post('/threats/check', { url }),
};
