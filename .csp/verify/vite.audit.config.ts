import { defineConfig, mergeConfig } from 'vite'
import base from '../../web/vite.config'
export default mergeConfig(base, defineConfig({
  server: {
    port: 5174,
    proxy: {
      '/api': { target: 'http://127.0.0.1:9133', changeOrigin: true },
      '/ws':  { target: 'ws://127.0.0.1:9133', ws: true },
    },
  },
}))
