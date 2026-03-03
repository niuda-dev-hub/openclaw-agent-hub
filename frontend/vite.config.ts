import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Admin UI 直接走后端 API，无中间层
    // 本地开发时通过 dev proxy 避免 CORS
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:8010',
        changeOrigin: true,
      },
    },
  },
})
