<template>
  <div class="bg-white rounded-2xl shadow-sm p-6 opacity-0 animate-fade-in-up stagger-4">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5">
      <div class="p-2 rounded-lg bg-red-100">
        <FeatherIcon name="alert-circle" class="w-5 h-5 text-red-600" />
      </div>
      <h3 class="text-base font-semibold text-gray-800">Items Needing Attention</h3>
    </div>

    <!-- Tabs -->
    <div class="flex flex-wrap gap-2 mb-5">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="[
          'inline-flex items-center gap-2 px-4 py-2.5 rounded-full text-sm font-medium transition-all',
          activeTab === tab.key
            ? 'bg-indigo-600 text-white shadow-md'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        ]"
        @click="activeTab = tab.key"
      >
        <FeatherIcon :name="tab.icon" class="w-4 h-4" />
        {{ tab.label }}
        <span :class="[
          'px-2 py-0.5 rounded-full text-xs min-w-[24px] text-center',
          activeTab === tab.key ? 'bg-white/20' : 'bg-gray-200'
        ]">
          {{ tab.items.length }}
        </span>
      </button>
    </div>

    <!-- Table Content -->
    <div class="max-h-96 overflow-y-auto rounded-xl">
      <div v-if="currentTab.items.length === 0" class="text-center py-12">
        <FeatherIcon name="check-circle" class="w-12 h-12 text-emerald-400 mx-auto mb-3" />
        <p class="text-gray-500">{{ currentTab.emptyMessage }}</p>
      </div>

      <table v-else class="w-full">
        <thead class="bg-gray-50 sticky top-0">
          <tr>
            <th
              v-for="col in currentTab.columns"
              :key="col.key"
              :class="[
                'px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider',
                col.sortable ? 'cursor-pointer hover:bg-gray-100 select-none' : ''
              ]"
              @click="col.sortable && toggleSort(col.key)"
            >
              <div class="flex items-center gap-1">
                {{ col.label }}
                <FeatherIcon
                  v-if="col.sortable"
                  :name="getSortIcon(col.key)"
                  :class="['w-3 h-3', sortState.field === col.key ? 'text-indigo-600' : 'text-gray-400']"
                />
              </div>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="row in sortedItems"
            :key="row.name"
            class="hover:bg-gray-50 transition-colors"
          >
            <td v-for="col in currentTab.columns" :key="col.key" class="px-4 py-3.5 text-sm">
              <!-- Link column -->
              <a
                v-if="col.type === 'link'"
                :href="getRowLink(row)"
                class="text-indigo-600 font-medium hover:underline"
              >
                {{ row[col.key] }}
              </a>

              <!-- Status column -->
              <StatusBadge
                v-else-if="col.type === 'status'"
                :status="String(row[col.key])"
              />

              <!-- Date column -->
              <span
                v-else-if="col.type === 'date'"
                :class="{ 'text-red-600 font-semibold': isOverdue(row[col.key]) }"
              >
                {{ formatDate(row[col.key]) }}
              </span>

              <!-- Currency column -->
              <span v-else-if="col.type === 'currency'">
                {{ formatCurrency(row[col.key]) }}
              </span>

              <!-- Default -->
              <span v-else class="text-gray-700">
                {{ row[col.key] || '-' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FeatherIcon } from 'frappe-ui'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({
  attention: {
    type: Object,
    default: () => ({}),
  },
})

const activeTab = ref('overdue-orders')
const sortState = ref({ field: '', order: 'asc' })

const tabs = computed(() => [
  {
    key: 'overdue-orders',
    label: 'Overdue Orders',
    icon: 'clock',
    items: props.attention?.overdue_orders || [],
    emptyMessage: 'No overdue orders - great job!',
    doctype: 'OPS Order',
    columns: [
      { key: 'ops_order_id', label: 'Order', type: 'link', sortable: true },
      { key: 'customer_name', label: 'Customer', sortable: true },
      { key: 'order_status', label: 'Status', type: 'status', sortable: true },
      { key: 'production_due_date', label: 'Due Date', type: 'date', sortable: true },
      { key: 'order_amount', label: 'Amount', type: 'currency', sortable: true },
    ],
  },
  {
    key: 'pending-proofs',
    label: 'Pending Proofs',
    icon: 'clock',
    items: props.attention?.orders_pending_proofs || [],
    emptyMessage: 'All proofs are approved!',
    doctype: 'OPS Order',
    columns: [
      { key: 'ops_order_id', label: 'Order', type: 'link', sortable: true },
      { key: 'customer_name', label: 'Customer', sortable: true },
      { key: 'pending_proof_count', label: 'Pending', type: 'status', sortable: true },
      { key: 'date_purchased', label: 'Date', type: 'date', sortable: true },
    ],
  },
  {
    key: 'pending-quotes',
    label: 'Pending Quotes',
    icon: 'file-text',
    items: props.attention?.pending_quotes || [],
    emptyMessage: 'No pending quotes',
    doctype: 'OPS Quote',
    columns: [
      { key: 'quote_id', label: 'Quote', type: 'link', sortable: true },
      { key: 'customer_name', label: 'Customer', sortable: true },
      { key: 'quote_status', label: 'Status', type: 'status', sortable: true },
      { key: 'quote_price', label: 'Value', type: 'currency', sortable: true },
      { key: 'quote_date', label: 'Date', type: 'date', sortable: true },
    ],
  },
  {
    key: 'overdue-proofs',
    label: 'Overdue Proofs',
    icon: 'alert-triangle',
    items: props.attention?.overdue_proofs || [],
    emptyMessage: 'No overdue proofs',
    doctype: 'OPS ZiFlow Proof',
    columns: [
      { key: 'proof_name', label: 'Proof', type: 'link', sortable: true },
      { key: 'order_id', label: 'Order', sortable: true },
      { key: 'proof_status', label: 'Status', type: 'status', sortable: true },
      { key: 'deadline', label: 'Deadline', type: 'date', sortable: true },
    ],
  },
])

const currentTab = computed(() =>
  tabs.value.find(t => t.key === activeTab.value) || tabs.value[0]
)

const sortedItems = computed(() => {
  const items = [...currentTab.value.items]
  if (!sortState.value.field) return items

  return items.sort((a, b) => {
    let va = a[sortState.value.field] || ''
    let vb = b[sortState.value.field] || ''

    // Handle numbers
    if (typeof va === 'number' && typeof vb === 'number') {
      return sortState.value.order === 'asc' ? va - vb : vb - va
    }

    // Handle strings
    va = String(va).toLowerCase()
    vb = String(vb).toLowerCase()

    if (va < vb) return sortState.value.order === 'asc' ? -1 : 1
    if (va > vb) return sortState.value.order === 'asc' ? 1 : -1
    return 0
  })
})

function toggleSort(field) {
  if (sortState.value.field === field) {
    sortState.value.order = sortState.value.order === 'asc' ? 'desc' : 'asc'
  } else {
    sortState.value.field = field
    sortState.value.order = 'asc'
  }
}

function getSortIcon(field) {
  if (sortState.value.field !== field) return 'chevrons-up-down'
  return sortState.value.order === 'asc' ? 'chevron-up' : 'chevron-down'
}

function getRowLink(row) {
  const doctype = currentTab.value.doctype.toLowerCase().replace(/ /g, '-')
  return `/app/${doctype}/${row.name}`
}

function formatDate(date) {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatCurrency(amount) {
  if (!amount) return '-'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
  }).format(amount)
}

function isOverdue(date) {
  if (!date) return false
  return new Date(date) < new Date()
}
</script>
