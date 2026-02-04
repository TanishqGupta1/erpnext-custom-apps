<template>
  <div class="flex flex-wrap gap-3 justify-center py-4">
    <a
      v-for="link in links"
      :key="link.href"
      :href="link.href"
      class="inline-flex items-center gap-2 px-5 py-2.5 bg-white rounded-full text-sm text-gray-600 border border-gray-200 transition-all duration-300 hover:bg-indigo-600 hover:text-white hover:border-indigo-600 hover:-translate-y-0.5 hover:shadow-lg"
    >
      <FeatherIcon :name="link.icon" class="w-4 h-4" />
      {{ link.label }}
    </a>
  </div>
</template>

<script setup>
import { FeatherIcon } from 'frappe-ui'

const links = [
  { href: '/app/ops-order', icon: 'shopping-cart', label: 'All Orders' },
  { href: '/app/ops-quote', icon: 'file-text', label: 'All Quotes' },
  { href: '/app/ops-ziflow-proof', icon: 'check-circle', label: 'All Proofs' },
  { href: '/app/ops-product', icon: 'box', label: 'Products' },
  { href: '/app/ops-customer', icon: 'users', label: 'Customers' },
  { href: '/app/ops-error-log', icon: 'alert-circle', label: 'Error Log' },
]
</script>
