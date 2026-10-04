/**
 * Configuración de API (Axios) para ISO Smart
 * Uses HttpOnly authentication cookies; JavaScript never handles JWT values.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

// Crear instancia de API - usar ruta relativa por defecto para que Vite/Nginx manejen el backend.
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Flag para evitar múltiples refreshes simultáneos
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve();
    }
  });
  failedQueue = [];
};

api.interceptors.request.use(
  (config) => {
    const requestUrl = config?.url || '';
    const unsafeMethod = !['get', 'head', 'options'].includes((config.method || 'get').toLowerCase());
    if (unsafeMethod && !requestUrl.includes('/auth/login/') && !requestUrl.includes('/auth/csrf/')) {
      const csrf = document.cookie.split('; ').find((item) => item.startsWith('csrftoken='))?.split('=')[1];
      if (csrf) {
        config.headers['X-CSRFToken'] = decodeURIComponent(csrf);
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor de response - manejar errores y refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = originalRequest?.url || '';
    const isAuthEndpoint = requestUrl.includes('/auth/login/') || requestUrl.includes('/auth/refresh/');

    // Si el error no es 401 o ya intentamos refresh, rechazar
    if (!originalRequest || error.response?.status !== 401 || originalRequest._retry || isAuthEndpoint) {
      return Promise.reject(error);
    }

    // Si ya estamos refrescando, encolar el request
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then(() => api(originalRequest))
        .catch(err => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      await api.post('/auth/refresh/');
      processQueue(null);
      return api(originalRequest);

    } catch (refreshError) {
      processQueue(refreshError, null);
      redirectToLogin();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

const redirectToLogin = () => {
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
};

export default api;
