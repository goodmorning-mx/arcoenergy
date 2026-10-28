import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  base: '/crm/',
  // gm-auth's built workspace includes its own React version. Deduplicate it
  // with the CRM renderer to keep hooks on the active React dispatcher.
  resolve: { dedupe: ['react', 'react-dom'] },
  server: { port: 5174 },
});
