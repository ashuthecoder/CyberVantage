import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static/react-build',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        landing: resolve(__dirname, 'src/pages/landing-main.jsx'),
        dashboard: resolve(__dirname, 'src/pages/dashboard-main.jsx'),
      },
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]'
      }
    },
  },
  base: '/static/react-build/',
})
