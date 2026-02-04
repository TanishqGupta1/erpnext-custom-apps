import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const loading = ref(true)
  const error = ref(null)
  const lastUpdated = ref(null)
  const autoRefreshEnabled = ref(true)
  
  // Data
  const overview = ref(null)
  const attention = ref(null)
  const charts = ref(null)
  const pipeline = ref(null)

  // Resources (Frappe UI pattern)
  const overviewResource = createResource({
    url: 'ops_ziflow.api.ops_dashboard.get_dashboard_overview',
    auto: false,
    onSuccess: (data) => {
      overview.value = data
    },
    onError: (err) => {
      error.value = err
    },
  })

  const attentionResource = createResource({
    url: 'ops_ziflow.api.ops_dashboard.get_attention_items',
    auto: false,
    onSuccess: (data) => {
      attention.value = data
    },
  })

  const chartsResource = createResource({
    url: 'ops_ziflow.api.ops_dashboard.get_charts_data',
    auto: false,
    params: { days: 30 },
    onSuccess: (data) => {
      charts.value = data
    },
  })

  const pipelineResource = createResource({
    url: 'ops_ziflow.api.ops_dashboard.get_pipeline_summary',
    auto: false,
    onSuccess: (data) => {
      pipeline.value = data
    },
  })

  // Computed
  const isLoading = computed(() => 
    overviewResource.loading || 
    attentionResource.loading || 
    chartsResource.loading || 
    pipelineResource.loading
  )

  const greeting = computed(() => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good Morning'
    if (hour < 17) return 'Good Afternoon'
    return 'Good Evening'
  })

  const entityCards = computed(() => {
    if (!overview.value) return []
    const o = overview.value
    return [
      {
        key: 'orders',
        label: 'Orders',
        value: o.total_orders || 0,
        icon: 'shopping-cart',
        gradient: 'from-indigo-500 to-purple-500',
        stats: [
          { label: 'Active', value: o.active_orders || 0 },
          { label: 'New', value: o.new_orders || 0, highlight: true },
          { label: 'Overdue', value: o.overdue_orders || 0, danger: true },
        ],
        revenue: o.orders_revenue || 0,
        route: 'ops-orders-dashboard',
      },
      {
        key: 'quotes',
        label: 'Quotes',
        value: o.total_quotes || 0,
        icon: 'file-text',
        gradient: 'from-emerald-500 to-teal-500',
        stats: [
          { label: 'Active', value: o.active_quotes || 0 },
          { label: 'Pending', value: o.pending_quotes || 0, highlight: true },
          { label: 'Sent', value: o.sent_quotes || 0 },
        ],
        revenue: o.quotes_value || 0,
        route: 'ops-quotes-dashboard',
      },
      {
        key: 'proofs',
        label: 'Proofs',
        value: o.total_proofs || 0,
        icon: 'check-circle',
        gradient: 'from-pink-500 to-rose-500',
        stats: [
          { label: 'Pending', value: o.pending_proofs || 0, highlight: true },
          { label: 'Approved', value: o.approved_proofs || 0 },
          { label: 'Overdue', value: o.overdue_proofs || 0, danger: true },
        ],
        route: 'ziflow-dashboard',
      },
      {
        key: 'products',
        label: 'Products',
        value: o.total_products || 0,
        icon: 'box',
        gradient: 'from-blue-500 to-cyan-500',
        stats: [
          { label: 'Active', value: o.active_products || 0 },
          { label: 'New', value: o.new_products || 0, highlight: true },
        ],
        route: '/app/ops-product',
      },
    ]
  })

  const todayStats = computed(() => {
    if (!overview.value) return { orders: 0, quotes: 0, proofs: 0 }
    return {
      orders: overview.value.orders_today || 0,
      quotes: overview.value.quotes_today || 0,
      proofs: overview.value.pending_proofs || 0,
    }
  })

  const monthStats = computed(() => {
    if (!overview.value) return { orders: 0, quotes: 0, revenue: 0 }
    return {
      orders: overview.value.orders_this_month || 0,
      quotes: overview.value.quotes_this_month || 0,
      revenue: overview.value.monthly_revenue || 0,
    }
  })

  // Actions
  async function fetchAll() {
    loading.value = true
    error.value = null
    
    try {
      await Promise.all([
        overviewResource.reload(),
        attentionResource.reload(),
        chartsResource.reload(),
        pipelineResource.reload(),
      ])
      lastUpdated.value = new Date()
    } catch (err) {
      error.value = err.message || 'Failed to load dashboard'
    } finally {
      loading.value = false
    }
  }

  function toggleAutoRefresh() {
    autoRefreshEnabled.value = !autoRefreshEnabled.value
  }

  return {
    // State
    loading,
    error,
    lastUpdated,
    autoRefreshEnabled,
    
    // Data
    overview,
    attention,
    charts,
    pipeline,
    
    // Computed
    isLoading,
    greeting,
    entityCards,
    todayStats,
    monthStats,
    
    // Actions
    fetchAll,
    toggleAutoRefresh,
  }
})
