import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import path from 'path'

export default defineConfig({
  plugins: [
    frappeui({
      lucideIcons: true,
    }),
    vue({
      script: {
        propsDestructure: true,
      },
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  build: {
    outDir: '../ops_ziflow/public/frontend',
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      input: {
        'cluster-dashboard': path.resolve(__dirname, 'src/main.js'),
      },
      output: {
        entryFileNames: '[name].bundle.js',
        chunkFileNames: '[name].[hash].js',
        assetFileNames: 'style.[ext]',
      },
    },
  },
  optimizeDeps: {
    include: ['frappe-ui', 'feather-icons', 'socket.io-client'],
  },
})
