<template>
  <div class="min-h-screen bg-slate-950 text-white selection:bg-purple-500/30">
    <!-- Aurora Background Blobs -->
    <div class="aurora-bg-blur top-[-10%] left-[-10%] w-[50%] h-[50%] bg-sky-500"></div>
    <div class="aurora-bg-blur bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-purple-600 animate-pulse-slow"></div>
    <div class="aurora-bg-blur top-[20%] right-[10%] w-[40%] h-[40%] bg-pink-500/20"></div>

    <div class="flex h-screen overflow-hidden">
      <!-- Sidebar -->
      <aside class="w-64 glass-card m-4 mr-0 flex flex-col items-center py-8 z-20">
        <div class="mb-12">
          <h1 class="text-2xl font-outfit aurora-text tracking-tighter">MIROFISH</h1>
        </div>

        <nav class="flex-1 w-full px-4 space-y-2">
          <router-link 
            v-for="item in menuItems" 
            :key="item.path"
            :to="item.path"
            class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group"
            :class="isActive(item.path) ? 'bg-white/10 text-sky-400' : 'text-slate-400 hover:text-white hover:bg-white/5'"
          >
            <component :is="item.icon" :size="20" class="group-hover:scale-110 transition-transform" />
            <span class="font-medium">{{ item.name }}</span>
          </router-link>
        </nav>

        <div class="mt-auto px-4 w-full">
          <div class="p-4 glass-card bg-sky-500/5 text-xs text-slate-400">
            <p>Cloud Synchronized</p>
            <div class="flex items-center gap-2 mt-1">
              <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              <span class="text-green-400 font-medium">Supabase Online</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="flex-1 overflow-y-auto p-4 custom-scrollbar relative">
        <header class="flex items-center justify-between mb-8 px-4">
          <div>
            <h2 class="text-sm font-medium text-slate-400 uppercase tracking-widest">{{ pageTitle }}</h2>
            <p class="text-2xl font-semibold">{{ pageSubtitle }}</p>
          </div>
          
          <div class="flex items-center gap-4">
            <button class="glass-card px-4 py-2 flex items-center gap-2 hover:bg-white/10 transition-all text-sm">
              <span class="w-2 h-2 rounded-full bg-sky-400"></span>
              English (Global)
            </button>
          </div>
        </header>

        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  LayoutDashboard, 
  FolderKanban, 
  Zap, 
  Settings, 
  Database,
  Globe
} from 'lucide-vue-next'

const route = useRoute()

const menuItems = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Projects', path: '/projects', icon: FolderKanban },
  { name: 'Real-time Stats', path: '/simulator', icon: Zap },
  { name: 'Ontology', path: '/ontology', icon: Globe },
  { name: 'Storage', path: '/storage', icon: Database },
  { name: 'Settings', path: '/settings', icon: Settings },
]

const isActive = (path) => route.path === path

const pageTitle = computed(() => {
  const current = menuItems.find(item => item.path === route.path)
  return current ? current.name : 'System'
})

const pageSubtitle = computed(() => {
  if (route.path === '/') return 'Welcome back, Architect'
  if (route.path === '/simulator') return 'Active Simulation Stream'
  return 'Cloud Environment'
})
</script>

<style scoped>
.router-link-active {
  @apply bg-white/10 text-sky-400 border-r-2 border-sky-400 shadow-lg shadow-sky-500/5;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  @apply bg-white/5 rounded-full hover:bg-white/10 transition-colors;
}
</style>
