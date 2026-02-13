// src/config.js

export const getApiBaseUrl = () => {
  // 1. Si existe una variable de entorno explícita (para producción real con dominio), úsala.
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  // 2. Autodescubrimiento para desarrollo local y red WiFi:
  // Toma el hostname actual del navegador (ej. 'localhost', '192.168.0.3')
  const hostname = window.location.hostname;
  
  // Asume que el backend siempre corre en el puerto 8001 (configurado en docker-compose)
  return `${window.location.protocol}//${hostname}:8001`;
};

export const API_BASE_URL = getApiBaseUrl();