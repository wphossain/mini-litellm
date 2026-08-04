import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Relative base path ensures HTML works regardless of route prefix
  base: './',
  server: {
    port: 3000,
    proxy: {
      '/v1': 'http://localhost:4000',
      '/admin': 'http://localhost:4000',
      '/health': 'http://localhost:4000',
    },
  },
  build: { outDir: 'dist', sourcemap: false },
})
