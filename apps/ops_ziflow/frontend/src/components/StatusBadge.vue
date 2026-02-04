<template>
  <span :class="badgeClasses">
    <span v-if="dot" :class="dotClasses" />
    {{ label || status }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: String,
  label: String,
  variant: String,
  dot: {
    type: Boolean,
    default: false,
  },
})

const variantMap = {
  danger: 'bg-red-50 text-red-700 ring-red-600/20',
  warning: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  success: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  info: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  purple: 'bg-purple-50 text-purple-700 ring-purple-600/20',
  gray: 'bg-gray-50 text-gray-700 ring-gray-600/20',
}

const dotMap = {
  danger: 'bg-red-500',
  warning: 'bg-amber-500',
  success: 'bg-emerald-500',
  info: 'bg-blue-500',
  purple: 'bg-purple-500',
  gray: 'bg-gray-500',
}

// Auto-detect variant from status
const statusVariantMap = {
  // Danger statuses
  'overdue': 'danger',
  'cancelled': 'danger',
  'rejected': 'danger',
  'failed': 'danger',
  'error': 'danger',
  // Warning statuses
  'pending': 'warning',
  'draft': 'warning',
  'awaiting': 'warning',
  'on hold': 'warning',
  // Success statuses
  'completed': 'success',
  'approved': 'success',
  'delivered': 'success',
  'paid': 'success',
  'active': 'success',
  // Info statuses
  'in progress': 'info',
  'processing': 'info',
  'sent': 'info',
  'shipped': 'info',
  // Purple statuses
  'new': 'purple',
  'quote': 'purple',
}

const resolvedVariant = computed(() => {
  if (props.variant) return props.variant
  const statusLower = (props.status || '').toLowerCase()
  return statusVariantMap[statusLower] || 'gray'
})

const badgeClasses = computed(() => [
  'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full',
  'text-xs font-semibold uppercase tracking-wide',
  'ring-1 ring-inset',
  variantMap[resolvedVariant.value] || variantMap.gray,
])

const dotClasses = computed(() => [
  'w-1.5 h-1.5 rounded-full',
  dotMap[resolvedVariant.value] || dotMap.gray,
])
</script>
