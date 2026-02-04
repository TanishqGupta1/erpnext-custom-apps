/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/components/**/*.{vue,js,ts}',
  ],
  theme: {
    extend: {
      colors: {
        ops: {
          primary: '#6366f1',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          info: '#3b82f6',
          purple: '#8b5cf6',
          pink: '#ec4899',
        },
      },
    },
  },
  plugins: [],
}
