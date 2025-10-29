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
      '/labeling': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: true
      },
      '/config.js': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/static': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: true
      },
      '/get_obj_image': {
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
