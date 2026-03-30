import axios from 'axios';

// Dynamic API URL configuration for custom domain support
// If running on custom domain (not preview), use relative path
// Otherwise use the environment variable
const getApiBaseUrl = () => {
  const envUrl = process.env.REACT_APP_BACKEND_URL;
  
  // If no env URL, use relative path
  if (!envUrl) return '';
  
  // Check if we're on the preview domain
  const isPreviewDomain = window.location.hostname.includes('preview.emergentagent.com');
  
  // If on custom domain (not preview), use relative path for API calls
  // This allows the proxy/ingress to handle routing
  if (!isPreviewDomain) {
    return '';
  }
  
  return envUrl;
};

const API_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_URL,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Normalize URLs - ensure single /api prefix
  if (config.url) {
    // Remove double /api/api if exists
    if (config.url.startsWith('/api/api')) {
      config.url = config.url.replace('/api/api', '/api');
    }
    // Add /api if not present and not external URL
    else if (!config.url.startsWith('/api') && !config.url.startsWith('http')) {
      config.url = '/api' + config.url;
    }
  }
  return config;
});

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;