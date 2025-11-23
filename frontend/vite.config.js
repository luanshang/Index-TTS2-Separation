import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    host: '0.0.0.0', // 监听所有网络接口
    allowedHosts: [
      'aa7-kegcm651vax9a9xu7-ivdz0wxi-custom.app.onethingai.internal',
      '.app.onethingai.internal', // 允许所有 .app.onethingai.internal 子域名
      'localhost',
      '127.0.0.1',
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:10080',
        changeOrigin: true,
      },
      '/outputs': {
        target: 'http://localhost:10080',
        changeOrigin: true,
      },
      '/voices': {
        target: 'http://localhost:10080',
        changeOrigin: true,
      },
      '/examples': {
        target: 'http://localhost:10080',
        changeOrigin: true,
      },
    },
  },
})
