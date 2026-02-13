import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
    optimizeDeps: {
    exclude: ['vue-plotly'] // Evita prebundling de vue-plotly
  },
  server: {
    host: '0.0.0.0', // Esto es clave
   port: 8081,
    // host: true,      // permite accesos desde la red
    open: false,     // opcional: no abrir navegador
    cors: true       // opcio
  },
  build: {
    outDir: 'dist',          // carpeta de salida del build
    sourcemap: true,         // útil para debug
  },
  css: {
  preprocessorOptions: {
    scss: {
      additionalData: `
        @use "@/assets/scss/_variables.scss" as *;
        @use "@/assets/scss/_global-responsive.scss" as *;

      `
    }
  }
},

  base: '/',                 // ruta base (importante para router con history)
})
        // @use "@/assets/scss/_mobile.scss" as *;
