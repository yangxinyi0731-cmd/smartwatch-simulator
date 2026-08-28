import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

const backendTarget = 'http://127.0.0.1:8000'
const backendProxy = {
  '/api': { target: backendTarget },
  '/ws': { target: backendTarget, ws: true },
}

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '127.0.0.1',
    proxy: backendProxy,
  },
  preview: {
    host: '127.0.0.1',
    proxy: backendProxy,
  },
})
