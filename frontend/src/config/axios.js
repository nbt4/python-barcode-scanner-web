import axios from 'axios';

const baseURL = '/api/v1';  // This matches our nginx configuration

const instance = axios.create({
  baseURL,
  timeout: 30000,  // Increased timeout for slower connections
  headers: {
    'Content-Type': 'application/json',
  },
  validateStatus: status => {
    return status >= 200 && status < 300; // Default
  },
});

// Add a request interceptor
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle 401s
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default instance;
