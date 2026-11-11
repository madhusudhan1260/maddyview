import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The browser only ever talks to the Vite origin; /api is proxied to FastAPI so the
// session cookie stays first-party and no backend URL or secret is shipped to the client.
const API_TARGET = process.env.FINPILOT_API_URL || 'http://127.0.0.1:8040'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5190,
    strictPort: true,
    proxy: { '/api': { target: API_TARGET, changeOrigin: false } },
  },
  preview: {
    port: 5190,
    strictPort: true,
    proxy: { '/api': { target: API_TARGET, changeOrigin: false } },
  },
})
