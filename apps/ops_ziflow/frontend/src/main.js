import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { FrappeUI, setConfig, frappeRequest } from 'frappe-ui'
import App from './App.vue'

// Configure Frappe UI to use Frappe backend
setConfig('resourceFetcher', frappeRequest)

// Function to mount the app
function mountApp() {
  const container = document.getElementById('ops-cluster-dashboard-vue')
  
  if (!container) {
    console.error('Vue mount point not found: #ops-cluster-dashboard-vue')
    return
  }
  
  // Check if already mounted
  if (container.__vue_app__) {
    console.log('Vue app already mounted')
    return
  }
  
  const pinia = createPinia()
  const app = createApp(App)
  
  app.use(FrappeUI)
  app.use(pinia)
  
  app.mount('#ops-cluster-dashboard-vue')
  console.log('OPS Vue Dashboard mounted successfully')
  
  // Expose for debugging
  window.__OPS_DASHBOARD__ = app
}

// Try to mount when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountApp)
} else {
  // DOM already loaded, but element might not exist yet
  // Use a small delay to ensure Frappe has rendered the page
  setTimeout(mountApp, 100)
}

// Also expose mount function globally for manual triggering
window.mountOPSDashboard = mountApp
