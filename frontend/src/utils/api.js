import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3001',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
};

// Devices API
export const devicesAPI = {
  create: (deviceData) => api.post('/devices/create', deviceData),
  list: () => api.get('/devices'),
  view: (deviceId, certType = 'device_cert') => api.get(`/devices/${deviceId}/view`, {
    params: { cert_type: certType }
  }),
  download: (deviceId) => api.get(`/devices/${deviceId}/download`, {
    responseType: 'blob',
  }),
  delete: (deviceId, password) => api.delete(`/devices/${deviceId}`, {
    params: { password }
  }),
};

// Health API
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
