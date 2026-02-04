<template>
  <div 
    :class="[
      'relative overflow-hidden rounded-2xl p-6 cursor-pointer',
      'transition-all duration-300 ease-out',
      'hover:-translate-y-2 hover:shadow-2xl',
      'bg-gradient-to-br', card.gradient,
      'opacity-0 animate-fade-in-up',
      staggerClass
    ]"
    @click="handleClick"
  >
    <!-- Background Icon -->
    <div class="absolute right-4 top-4 opacity-20 transition-all duration-300 group-hover:opacity-40 group-hover:scale-110">
      <FeatherIcon :name="card.icon" class="w-16 h-16 text-white" />
    </div>

    <!-- Label -->
    <p class="text-xs font-medium text-white/80 uppercase tracking-wider mb-1">
      {{ card.label }}
    </p>

    <!-- Main Value -->
    <p class="text-5xl font-extrabold text-white leading-none mb-3">
      {{ formatNumber(card.value) }}
    </p>

    <!-- Stats Row -->
    <div class="flex gap-5 text-sm text-white/90 mb-2">
      <span v-for="stat in card.stats" :key="stat.label">
        {{ stat.label }}: 
        <strong :class="{ 
          'text-yellow-200': stat.highlight, 
          'text-red-300': stat.danger 
        }">
          {{ stat.value }}
        </strong>
      </span>
    </div>

    <!-- Revenue (if present) -->
    <div 
      v-if="card.revenue !== undefined" 
      class="text-xl font-bold text-white mt-2 pt-3 border-t border-white/20"
    >
      {{ formatCurrency(card.revenue) }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  card: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['click'])

const staggerClass = computed(() => `stagger-${props.index + 1}`)

function formatNumber(num) {
  if (num === null || num === undefined) return '0'
  return num.toLocaleString()
}

function formatCurrency(amount) {
  if (!amount) return '$0'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

function handleClick() {
  emit('click', props.card)
  if (props.card.route) {
    if (props.card.route.startsWith('/')) {
      window.location.href = props.card.route
    } else {
      frappe.set_route(props.card.route)
    }
  }
}
</script>
