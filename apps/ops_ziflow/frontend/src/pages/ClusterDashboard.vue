<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
    <!-- Loading State -->
    <LoadingSkeleton v-if="store.loading && !store.overview" />

    <!-- Dashboard Content -->
    <template v-else>
      <!-- Header -->
      <header class="mb-6 opacity-0 animate-fade-in-up">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-800">{{ store.greeting }}</h1>
            <p class="text-sm text-gray-500 flex items-center gap-4 mt-1">
              <span>OPS Dashboard Overview</span>
              <span v-if="store.lastUpdated" class="text-xs text-gray-400">
                Last updated: {{ formatTime(store.lastUpdated) }}
              </span>
            </p>
          </div>
          <div class="flex items-center gap-3">
            <Button
              variant="outline"
              :class="{ 'ring-2 ring-emerald-500': store.autoRefreshEnabled }"
              @click="store.toggleAutoRefresh"
            >
              <template #prefix>
                <FeatherIcon
                  name="refresh-cw"
                  :class="['w-4 h-4', store.autoRefreshEnabled ? 'text-emerald-600' : '']"
                />
              </template>
              Auto-refresh {{ store.autoRefreshEnabled ? 'On' : 'Off' }}
            </Button>
            <Button
              variant="solid"
              :loading="store.isLoading"
              @click="refresh"
            >
              <template #prefix>
                <FeatherIcon name="refresh-cw" class="w-4 h-4" />
              </template>
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <!-- Entity Cards Grid -->
      <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
        <EntityCard
          v-for="(card, index) in store.entityCards"
          :key="card.key"
          :card="card"
          :index="index"
        />
      </section>

      <!-- Stats Panels Row -->
      <section class="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
        <StatPanel
          title="Today's Activity"
          icon="sun"
          icon-color="indigo"
          :stats="[
            { label: 'Orders', value: store.todayStats.orders, colorClass: 'text-indigo-600' },
            { label: 'Quotes', value: store.todayStats.quotes, colorClass: 'text-emerald-600' },
            { label: 'Pending Proofs', value: store.todayStats.proofs, colorClass: 'text-pink-600' },
          ]"
          :stagger="1"
        />
        <StatPanel
          title="This Month"
          icon="calendar"
          icon-color="emerald"
          :stats="[
            { label: 'Orders', value: store.monthStats.orders, colorClass: 'text-indigo-600' },
            { label: 'Quotes', value: store.monthStats.quotes, colorClass: 'text-emerald-600' },
            { label: 'Revenue', value: store.monthStats.revenue, format: 'currency', colorClass: 'text-emerald-600' },
          ]"
          :stagger="2"
        />
      </section>

      <!-- Pipeline Row -->
      <section class="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
        <div class="bg-white rounded-2xl shadow-sm p-6 opacity-0 animate-fade-in-up stagger-3">
          <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-lg bg-indigo-100">
                <FeatherIcon name="layers" class="w-5 h-5 text-indigo-600" />
              </div>
              <h3 class="text-base font-semibold text-gray-800">Order Pipeline</h3>
            </div>
            <span
              class="text-xs text-indigo-600 cursor-pointer hover:text-indigo-800"
              @click="navigateTo('ops-orders-dashboard')"
            >
              View All
            </span>
          </div>
          <PipelineChart
            v-if="store.pipeline?.orders"
            :data="store.pipeline.orders"
            type="orders"
          />
          <div v-else class="h-24 flex items-center justify-center text-gray-400">
            No pipeline data
          </div>
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6 opacity-0 animate-fade-in-up stagger-3">
          <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-lg bg-emerald-100">
                <FeatherIcon name="file-text" class="w-5 h-5 text-emerald-600" />
              </div>
              <h3 class="text-base font-semibold text-gray-800">Quote Pipeline</h3>
            </div>
            <span
              class="text-xs text-emerald-600 cursor-pointer hover:text-emerald-800"
              @click="navigateTo('ops-quotes-dashboard')"
            >
              View All
            </span>
          </div>
          <PipelineChart
            v-if="store.pipeline?.quotes"
            :data="store.pipeline.quotes"
            type="quotes"
          />
          <div v-else class="h-24 flex items-center justify-center text-gray-400">
            No pipeline data
          </div>
        </div>
      </section>

      <!-- Charts Row -->
      <section class="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-6">
        <div class="bg-white rounded-2xl shadow-sm p-6 opacity-0 animate-fade-in-up stagger-3">
          <div class="flex items-center gap-3 mb-5">
            <div class="p-2 rounded-lg bg-blue-100">
              <FeatherIcon name="trending-up" class="w-5 h-5 text-blue-600" />
            </div>
            <h3 class="text-base font-semibold text-gray-800">Activity Timeline</h3>
            <span class="text-xs text-gray-400 ml-auto">Last 30 Days</span>
          </div>
          <div ref="activityChartRef" class="h-64" />
        </div>

        <div class="bg-white rounded-2xl shadow-sm p-6 opacity-0 animate-fade-in-up stagger-3">
          <div class="flex items-center gap-3 mb-5">
            <div class="p-2 rounded-lg bg-purple-100">
              <FeatherIcon name="pie-chart" class="w-5 h-5 text-purple-600" />
            </div>
            <h3 class="text-base font-semibold text-gray-800">Status Distribution</h3>
          </div>
          <div class="grid grid-cols-2 gap-6">
            <div class="text-center">
              <div ref="ordersChartRef" class="h-44" />
              <p class="text-xs text-gray-500 uppercase tracking-wide mt-2">Orders</p>
            </div>
            <div class="text-center">
              <div ref="proofsChartRef" class="h-44" />
              <p class="text-xs text-gray-500 uppercase tracking-wide mt-2">Proofs</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Attention Items -->
      <AttentionTabs :attention="store.attention" />

      <!-- Quick Links -->
      <section class="mt-6">
        <div class="bg-white rounded-2xl shadow-sm opacity-0 animate-fade-in-up stagger-4">
          <QuickLinks />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'
import { useDashboardStore } from '@/stores/dashboard'

import LoadingSkeleton from '@/components/LoadingSkeleton.vue'
import EntityCard from '@/components/EntityCard.vue'
import StatPanel from '@/components/StatPanel.vue'
import PipelineChart from '@/components/PipelineChart.vue'
import AttentionTabs from '@/components/AttentionTabs.vue'
import QuickLinks from '@/components/QuickLinks.vue'

const store = useDashboardStore()

// Chart refs
const activityChartRef = ref(null)
const ordersChartRef = ref(null)
const proofsChartRef = ref(null)

// Auto-refresh interval
let refreshInterval = null

onMounted(async () => {
  await store.fetchAll()
  startAutoRefresh()

  // Render charts after data loads
  await nextTick()
  renderCharts()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

// Watch for chart data changes
watch(() => store.charts, () => {
  nextTick(() => renderCharts())
}, { deep: true })

watch(() => store.autoRefreshEnabled, (enabled) => {
  if (enabled) {
    startAutoRefresh()
    frappe.show_alert({ message: 'Auto-refresh enabled (5 min)', indicator: 'green' })
  } else {
    if (refreshInterval) clearInterval(refreshInterval)
    frappe.show_alert({ message: 'Auto-refresh disabled', indicator: 'orange' })
  }
})

function startAutoRefresh() {
  if (refreshInterval) clearInterval(refreshInterval)
  if (store.autoRefreshEnabled) {
    refreshInterval = setInterval(() => {
      store.fetchAll()
    }, 300000) // 5 minutes
  }
}

async function refresh() {
  await store.fetchAll()
  frappe.show_alert({ message: 'Dashboard updated', indicator: 'green' }, 2)
}

function formatTime(date) {
  if (!date) return ''
  return new Date(date).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

function navigateTo(route) {
  frappe.set_route(route)
}

function renderCharts() {
  // Activity Timeline Chart
  if (activityChartRef.value && store.charts?.timeline) {
    const timeline = store.charts.timeline
    new frappe.Chart(activityChartRef.value, {
      type: 'line',
      height: 250,
      colors: ['#6366f1', '#10b981', '#ec4899'],
      data: {
        labels: timeline.labels || [],
        datasets: [
          { name: 'Orders', values: timeline.orders || [] },
          { name: 'Quotes', values: timeline.quotes || [] },
          { name: 'Proofs', values: timeline.proofs || [] },
        ],
      },
      lineOptions: {
        hideDots: 0,
        regionFill: 1,
        spline: 1,
      },
      axisOptions: {
        xIsSeries: true,
      },
    })
  }

  // Orders Status Chart
  if (ordersChartRef.value && store.overview?.orders_by_status) {
    const statuses = store.overview.orders_by_status
    new frappe.Chart(ordersChartRef.value, {
      type: 'pie',
      height: 180,
      colors: ['#6366f1', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ef4444'],
      data: {
        labels: Object.keys(statuses),
        datasets: [{ values: Object.values(statuses) }],
      },
    })
  }

  // Proofs Status Chart
  if (proofsChartRef.value && store.overview?.proofs_by_status) {
    const statuses = store.overview.proofs_by_status
    new frappe.Chart(proofsChartRef.value, {
      type: 'pie',
      height: 180,
      colors: ['#ec4899', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'],
      data: {
        labels: Object.keys(statuses),
        datasets: [{ values: Object.values(statuses) }],
      },
    })
  }
}
</script>
