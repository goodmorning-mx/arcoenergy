import React from 'react';
import ReactDOM from 'react-dom/client';
import { PwaRuntime } from '@goodmorning/gm-pwa';
import { AuthProvider, createAuthClient } from '@goodmorning/gm-auth';
import App from './App';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <AuthProvider client={createAuthClient(import.meta.env.VITE_API_URL || '/api')}>
      <PwaRuntime config={{ appName: 'ArcoEnergy Campo', version: '0.1.0', serviceWorkerUrl: `${import.meta.env.BASE_URL}sw.js` }}><App /></PwaRuntime>
    </AuthProvider>
  </React.StrictMode>,
);
