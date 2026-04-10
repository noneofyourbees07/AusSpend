import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // GitHub Pages serves at https://USER.github.io/AusSpend/
  // so production builds need /AusSpend/ as the base path.
  // Dev server uses / so localhost:5173 works as expected.
  base: command === 'build' ? '/AusSpend/' : '/',
  server: {
    proxy: {
      // Optional Flask backend during development (no longer required)
      '/api': 'http://localhost:5000',
    },
  },
}))
