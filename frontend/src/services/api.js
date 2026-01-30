/**
 * Configuración de API (Axios) para ISO Smart
 * Incluye interceptores para manejo automático de tokens JWT
 */

import axios from 'axios';

// Crear instancia de API
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://isosmart.local/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag para evitar múltiples refreshes simultáneos
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Interceptor de request - agregar token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
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

    // Si el error no es 401 o ya intentamos refresh, rechazar
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // Si ya estamos refrescando, encolar el request
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        })
        .catch(err => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      // No hay refresh token, redirigir a login
      isRefreshing = false;
      redirectToLogin();
      return Promise.reject(error);
    }

    try {
      const response = await api.post('/auth/refresh/', {
        refresh: refreshToken,
      });

      const { access, refresh: newRefresh } = response.data;

      // Guardar nuevos tokens
      localStorage.setItem('access_token', access);
      if (newRefresh) {
        localStorage.setItem('refresh_token', newRefresh);
      }

      // Actualizar header por defecto
      api.defaults.headers.common['Authorization'] = `Bearer ${access}`;

      // Procesar cola de requests fallidos
      processQueue(null, access);

      // Reintentar request original
      originalRequest.headers.Authorization = `Bearer ${access}`;
      return api(originalRequest);

    } catch (refreshError) {
      processQueue(refreshError, null);
      
      // Limpiar tokens y redirigir a login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      delete api.defaults.headers.common['Authorization'];
      
      redirectToLogin();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

// Función para redirigir a login
const redirectToLogin = () => {
  // Solo redirigir si no estamos ya en login
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
};

export default api;
