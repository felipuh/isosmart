import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3001,
    strictPort: false,  // Si 3001 está ocupado, usa el siguiente puerto disponible
    allowedHosts: ['isosmart.local', 'localhost', '127.0.0.1', '192.168.100.100'],
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
