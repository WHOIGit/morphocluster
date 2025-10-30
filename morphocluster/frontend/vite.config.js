import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/morphocluster/frontend/',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 8080,
    proxy: {
      '/morphocluster/frontend/labeling': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: true
      },
      '/morphocluster/frontend/config.js': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/morphocluster/frontend/static': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/morphocluster/frontend/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: true
      },
      '/morphocluster/frontend/get_obj_image': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false
  }
})
