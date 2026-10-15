// v1.33.0 (AUDIT-F-06): process.env access in vite.config.ts. Declared
// minimally so `tsc -b` type-checks without requiring @types/node in the
// tsconfig.node.json types field.
declare const process: { env: Record<string, string | undefined> }

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      open: false,
      gzipSize: true,
      brotliSize: true,
      filename: '../.planning/bundle-analysis/stats.html'
    })
  ],
  server: {
    port: 5173,
    proxy: {
      // v1.33.0 (AUDIT-F-06): proxy target via env so dev can point at any
      // `saw web` port (default :8000 for backward compat).
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: (process.env.VITE_API_TARGET || 'http://localhost:8000').replace(/^http/, 'ws'),
        ws: true,
      },
    },
  },
})