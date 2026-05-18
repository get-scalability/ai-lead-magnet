import ImportMetaEnvPlugin from '@import-meta-env/unplugin'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const apiProxyTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:9610'

export default defineConfig({
  plugins: [
    react(),
    // eslint-disable-next-line import-x/no-named-as-default-member
    ImportMetaEnvPlugin.vite({ example: '.env.example' }),
  ],
  server: {
    proxy: {
      '/agents': {
        changeOrigin: true,
        target: apiProxyTarget,
      },
      '/api': {
        changeOrigin: true,
        target: apiProxyTarget,
      },
      '/auth': {
        changeOrigin: true,
        target: apiProxyTarget,
      },
    },
  },
})
