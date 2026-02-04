<template>
  <div class="space-y-4">
    <!-- Pipeline Bar -->
    <div class="flex gap-1 h-3 rounded-lg overflow-hidden bg-gray-100">
      <div
        v-for="(segment, idx) in segments"
        :key="segment.status"
        :style="{ width: segment.percentage + '%', backgroundColor: segment.color }"
        :title="`${segment.status}: ${segment.count}`"
        class="rounded transition-all duration-300 hover:scale-y-150 cursor-pointer"
        @click="$emit('segmentClick', segment)"
      />
    </div>

    <!-- Legend -->
    <div class="flex flex-wrap gap-x-4 gap-y-2">
      <div 
        v-for="segment in segments" 
        :key="segment.status"
        class="flex items-center gap-2 text-sm text-gray-600"
      >
        <span 
          class="w-3 h-3 rounded" 
          :style="{ backgroundColor: segment.color }"
        />
        <span>{{ segment.status }}</span>
        <strong class="text-gray-800">{{ segment.count }}</strong>
        <span v-if="segment.value" class="text-gray-400">
          ({{ formatCurrency(segment.value) }})
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
  type: {
    type: String,
    default: 'orders', // 'orders' or 'quotes'
  },
})

defineEmits(['segmentClick'])

const colorPalette = {
  orders: {
    'Draft': '#94a3b8',
    'Pending': '#f59e0b',
    'In Production': '#3b82f6',
    'Ready': '#10b981',
    'Shipped': '#8b5cf6',
    'Delivered': '#059669',
    'Completed': '#047857',
    'Cancelled': '#ef4444',
  },
  quotes: {
    'Draft': '#94a3b8',
    'Pending': '#f59e0b',
    'Sent': '#3b82f6',
    'Accepted': '#10b981',
    'Converted': '#8b5cf6',
    'Rejected': '#ef4444',
    'Expired': '#6b7280',
  },
}

const segments = computed(() => {
  if (!props.data || !props.data.by_status) return []
  
  const byStatus = props.data.by_status
  const total = Object.values(byStatus).reduce((sum, item) => {
    return sum + (typeof item === 'object' ? item.count : item)
  }, 0)
  
  if (total === 0) return []

  const colors = colorPalette[props.type] || colorPalette.orders
  
  return Object.entries(byStatus)
    .filter(([_, val]) => (typeof val === 'object' ? val.count : val) > 0)
    .map(([status, val]) => {
      const count = typeof val === 'object' ? val.count : val
      const value = typeof val === 'object' ? val.value : null
      return {
        status,
        count,
        value,
        percentage: (count / total) * 100,
        color: colors[status] || '#94a3b8',
      }
    })
    .sort((a, b) => b.count - a.count)
})

function formatCurrency(amount) {
  if (!amount) return ''
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
  }).format(amount)
}
</script>
