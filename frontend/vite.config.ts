import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: process.env.VITE_BASE_PATH ?? '/',
  // gm-auth is built from a nested workspace that has its own React install.
  // Force every module to use this app's React singleton or hooks run outside
  // ReactDOM's dispatcher and the whole PWA renders blank.
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  server: {
    port: 5173,
  },
});
