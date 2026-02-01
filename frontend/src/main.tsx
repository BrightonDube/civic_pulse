import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import { Workbox } from 'workbox-window';
import "leaflet/dist/leaflet.css";

if ('serviceWorker' in navigator) {
  const wb = new Workbox('/sw.js');
  wb.register();
}


ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
