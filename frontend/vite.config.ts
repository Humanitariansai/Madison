import path from 'path';
import tailwindcss from "@tailwindcss/vite"
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  return {
    server: {
      host: true,
      port: 5173,
      strictPort: true,
      proxy: {
        '/brandkit': {
          target: 'http://backend:8000',
          changeOrigin: true,
        },
        '/brandkits': {
          target: 'http://backend:8000',
          changeOrigin: true,
        },
        '/projects': {
          target: 'http://backend:8000',
          changeOrigin: true,
        },
      },
    },
    plugins: [react(), tailwindcss()],
    define: {
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      }
    }
  };
});
