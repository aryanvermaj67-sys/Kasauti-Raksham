import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8000', '/demo': 'http://localhost:8000' },
    fs: { allow: ['..'] }, // the message templates live in backend/app/templates (one source for UI and backend)
  },
})
