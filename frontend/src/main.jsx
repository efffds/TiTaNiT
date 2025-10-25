// src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import App from './App.jsx'
import Login from './pages/Login.jsx'
import Signup from './pages/Signup.jsx'
import Home from './pages/Home.jsx'
import './index.css'

async function bootstrap() {
  try {
    if (import.meta.env.VITE_USE_MOCK === "1") {
      const { worker } = await import('./mocks/browser');
      await worker.start({
        onUnhandledRequest: 'bypass',
        serviceWorker: { url: '/mockServiceWorker.js' }, // важно!
      });
    }
  } catch (e) {
    console.warn('MSW failed to start, continuing without mocks', e);
  } finally {
    ReactDOM.createRoot(document.getElementById('root')).render(
      <React.StrictMode>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<App />}>
              <Route index element={<Navigate to="/home" />} />
              <Route path="login" element={<Login />} />
              <Route path="signup" element={<Signup />} />
              <Route path="home" element={<Home />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </React.StrictMode>,
    );
  }
}

bootstrap();
