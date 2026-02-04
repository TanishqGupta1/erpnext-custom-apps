<template>
  <div class="space-y-6 p-6">
    <!-- Header Skeleton -->
    <div class="space-y-2">
      <div class="h-8 w-48 bg-gray-200 rounded animate-pulse" />
      <div class="h-4 w-32 bg-gray-200 rounded animate-pulse" />
    </div>

    <!-- Cards Skeleton -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
      <div 
        v-for="i in 4" 
        :key="i"
        class="h-40 rounded-2xl bg-gradient-to-br from-gray-200 to-gray-300 animate-pulse"
      />
    </div>

    <!-- Panels Skeleton -->
    <div class="grid grid-cols-2 gap-5">
      <div 
        v-for="i in 2" 
        :key="i"
        class="h-48 bg-white rounded-2xl shadow-sm animate-pulse"
      >
        <div class="p-6 space-y-4">
          <div class="h-5 w-32 bg-gray-200 rounded" />
          <div class="grid grid-cols-3 gap-4">
            <div v-for="j in 3" :key="j" class="h-20 bg-gray-100 rounded-xl" />
          </div>
        </div>
      </div>
    </div>

    <!-- Charts Skeleton -->
    <div class="grid grid-cols-2 gap-5">
      <div class="h-72 bg-white rounded-2xl shadow-sm animate-pulse p-6">
        <div class="h-5 w-40 bg-gray-200 rounded mb-4" />
        <div class="h-52 bg-gray-100 rounded-xl" />
      </div>
      <div class="h-72 bg-white rounded-2xl shadow-sm animate-pulse p-6">
        <div class="h-5 w-40 bg-gray-200 rounded mb-4" />
        <div class="h-52 bg-gray-100 rounded-xl" />
      </div>
    </div>

    <!-- Table Skeleton -->
    <div class="bg-white rounded-2xl shadow-sm animate-pulse p-6">
      <div class="h-5 w-48 bg-gray-200 rounded mb-4" />
      <div class="flex gap-2 mb-4">
        <div v-for="i in 4" :key="i" class="h-10 w-32 bg-gray-100 rounded-full" />
      </div>
      <div class="space-y-3">
        <div v-for="i in 5" :key="i" class="h-12 bg-gray-100 rounded" />
      </div>
    </div>
  </div>
</template>
