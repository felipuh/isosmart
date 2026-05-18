import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
      cssCodeSplit: true,
      modulePreload: { polyfill: false },
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Keep i18n catalog out of the app entry chunk.
          if (id.includes('/src/context/I18nContext.jsx')) {
            return 'app-i18n';
          }

          if (id.includes('node_modules/')) {
            if (
              id.includes('/react/') ||
              id.includes('/react-dom/') ||
              id.includes('/scheduler/') ||
              id.includes('/react-router/') ||
              id.includes('/react-router-dom/')
            ) {
              return 'vendor-react';
            }

            if (id.includes('/lucide-react/')) {
              return 'vendor-lucide';
            }

            if (
              id.includes('/i18next/') ||
              id.includes('/react-i18next/') ||
              id.includes('/i18next-browser-languagedetector/')
            ) {
              return 'vendor-i18n';
            }

            if (
              id.includes('/axios/') ||
              id.includes('/qs/') ||
              id.includes('/form-data/')
            ) {
              return 'vendor-network';
            }

            return 'vendor-misc';
          }

          if (id.includes('/src/components/Dashboard/') || id.includes('/src/pages/Dashboard')) {
            return 'dashboard-core';
          }

          if (id.includes('/src/features/operations/')) {
            return 'feature-operations';
          }

          if (id.includes('/src/features/performance/')) {
            return 'feature-performance';
          }

          if (id.includes('/src/features/improvement/')) {
            return 'feature-improvement';
          }

          if (id.includes('/src/features/resources/')) {
            return 'feature-resources';
          }

          if (id.includes('/src/features/leadership/')) {
            return 'feature-leadership';
          }

          if (id.includes('/src/features/planning/')) {
            return 'feature-planning';
          }
        },
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3001,
    strictPort: false,  // Si 3001 está ocupado, usa el siguiente puerto disponible
    hmr: {
      protocol: 'ws',
      host: process.env.VITE_HMR_HOST || 'isosmart.smart3ai.local',
      clientPort: Number(process.env.VITE_HMR_CLIENT_PORT || 80),
    },
    allowedHosts: [
      'isosmart.local',
      'isosmart.smart3ai.local',
      'smart3ai.local',
      'localhost',
      '127.0.0.1',
      '192.168.100.100',
    ],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
        rewrite: (path) => path,  // No reescribe el path
        ws: true,  // Soportar WebSockets si es necesario
      },
    },
    cors: true,  // Habilitar CORS en dev
  },
})
