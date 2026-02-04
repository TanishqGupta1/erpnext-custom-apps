<template>
  <div 
    :class="[
      'bg-white rounded-2xl p-6 shadow-sm',
      'transition-all duration-300 hover:shadow-lg',
      'opacity-0 animate-fade-in-up',
      staggerClass
    ]"
  >
    <!-- Header -->
    <div class="flex items-center justify-between mb-5">
      <div class="flex items-center gap-3">
        <div :class="['p-2 rounded-lg', iconBgClass]">
          <FeatherIcon :name="icon" :class="['w-5 h-5', iconClass]" />
        </div>
        <h3 class="text-base font-semibold text-gray-800">{{ title }}</h3>
      </div>
      <span 
        v-if="actionLabel" 
        class="text-xs text-indigo-600 cursor-pointer hover:text-indigo-800 transition-colors"
        @click="$emit('action')"
      >
        {{ actionLabel }}
      </span>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-3 gap-4">
      <div 
        v-for="stat in stats" 
        :key="stat.label"
        class="text-center p-4 bg-gray-50 rounded-xl transition-all hover:bg-gray-100 hover:-translate-y-0.5"
      >
        <p :class="['text-3xl font-bold leading-none mb-1', stat.colorClass || 'text-gray-800']">
          {{ formatValue(stat.value, stat.format) }}
        </p>
        <p class="text-xs text-gray-500 uppercase tracking-wide">
          {{ stat.label }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'

const props = defineProps({
  title: String,
  icon: String,
  iconColor: {
    type: String,
    default: 'indigo',
  },
  stats: Array,
  actionLabel: String,
  stagger: {
    type: Number,
    default: 1,
  },
})

defineEmits(['action'])

const staggerClass = computed(() => `stagger-${props.stagger}`)

const colorMap = {
  indigo: { bg: 'bg-indigo-100', icon: 'text-indigo-600' },
  emerald: { bg: 'bg-emerald-100', icon: 'text-emerald-600' },
  pink: { bg: 'bg-pink-100', icon: 'text-pink-600' },
  blue: { bg: 'bg-blue-100', icon: 'text-blue-600' },
}

const iconBgClass = computed(() => colorMap[props.iconColor]?.bg || 'bg-indigo-100')
const iconClass = computed(() => colorMap[props.iconColor]?.icon || 'text-indigo-600')

function formatValue(value, format) {
  if (format === 'currency') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value || 0)
  }
  return (value || 0).toLocaleString()
}
</script>
