<template>
  <div class="h-full flex flex-col space-y-4 font-inter">
    <!-- Status Header -->
    <div class="glass-card p-4 flex items-center justify-between border-sky-500/20 bg-sky-500/5">
      <div class="flex items-center gap-3">
        <div class="relative">
          <div class="w-3 h-3 rounded-full bg-sky-500 animate-ping absolute"></div>
          <div class="w-3 h-3 rounded-full bg-sky-500 relative"></div>
        </div>
        <div>
          <p class="text-xs font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">Reality Stream</p>
          <h4 class="font-semibold text-sky-400">{{ simulationId }}</h4>
        </div>
      </div>
      
      <div class="text-right">
        <p class="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Current Status</p>
        <p class="text-sm font-outfit font-bold text-white">{{ statusText }}</p>
      </div>
    </div>

    <!-- Live Logs Feed -->
    <div class="flex-1 glass-card bg-slate-950/50 overflow-hidden flex flex-col relative group">
      <div class="absolute inset-0 bg-gradient-to-b from-sky-500/5 to-transparent pointer-events-none"></div>
      
      <div class="p-3 border-b border-white/5 flex items-center justify-between bg-white/5">
        <span class="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-2">
          <Layers :size="12" /> Event Stream
        </span>
        <span class="text-[10px] text-slate-400 font-mono">{{ actions.length }} Events Captured</span>
      </div>

      <div ref="scrollContainer" class="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
        <transition-group name="list">
          <div v-for="action in actions" :key="action.id" 
               class="flex gap-3 text-sm animate-in slide-in-from-left-2 duration-300">
            <span class="text-slate-600 font-mono text-[10px] pt-1 whitespace-nowrap">
              {{ formatTime(action.timestamp) }}
            </span>
            <div class="flex-1 space-y-1">
              <div class="flex items-center gap-2">
                <span :class="platformClass(action.platform)" class="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-tighter">
                  {{ action.platform }}
                </span>
                <span class="text-slate-300 font-bold text-xs">{{ action.agent_name }}</span>
                <span class="text-slate-500 text-[10px]">• Round {{ action.round_num }}</span>
              </div>
              <p class="text-slate-400 leading-relaxed bg-white/5 p-2 rounded-lg border border-white/5 group-hover:border-white/10 transition-colors">
                <span class="text-sky-400 font-medium">{{ action.action_type }}</span>: 
                {{ formatArgs(action.action_args) }}
              </p>
            </div>
          </div>
        </transition-group>
        
        <div v-if="actions.length === 0" class="h-full flex flex-col items-center justify-center text-slate-600 space-y-4 opacity-50">
          <Database :size="48" class="animate-pulse" />
          <p class="text-sm font-medium">Waiting for cloud events...</p>
        </div>
      </div>
    </div>

    <!-- Controls -->
    <div class="grid grid-cols-2 gap-3">
      <button @click="$emit('stop')" class="glass-card py-3 flex items-center justify-center gap-2 text-red-400 hover:bg-red-500/10 transition-colors border-red-500/20">
        <Square :size="16" fill="currentColor" />
        <span class="font-bold text-xs uppercase tracking-widest">Terminate</span>
      </button>
      <button @click="$emit('next')" class="aurora-btn py-3 flex items-center justify-center gap-2 text-xs uppercase tracking-widest">
        <span>Gen Analysis</span>
        <ArrowRight :size="16" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Layers, Database, Square, ArrowRight } from 'lucide-vue-next'
import { supabase } from '../../supabase'

const props = defineProps({
  simulationId: { type: String, required: true },
  status: { type: String, default: 'running' }
})

const actions = ref([])
const scrollContainer = ref(null)
let subscription = null

const statusText = computed(() => {
  if (props.status === 'completed') return 'Simulation Completed'
  if (props.status === 'failed') return 'System Error'
  return 'Streaming Engine...'
})

const formatTime = (ts) => {
  const d = new Date(ts)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
}

const platformClass = (p) => {
  if (p === 'twitter') return 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
  return 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
}

const formatArgs = (args) => {
  if (!args) return ''
  if (args.content) return args.content
  if (args.text) return args.text
  return JSON.stringify(args)
}

const scrollToBottom = async () => {
  await nextTick()
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
  }
}

const subscribeToLogs = () => {
  console.log(`Subscribing to real-time logs for simulation: ${props.simulationId}`)
  
  subscription = supabase
    .channel(`live-logs-${props.simulationId}`)
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'agent_actions',
        filter: `simulation_id=eq.${props.simulationId}`
      },
      (payload) => {
        actions.value.push(payload.new)
        if (actions.value.length > 100) actions.value.shift()
        scrollToBottom()
      }
    )
    .subscribe()
}

onMounted(async () => {
  // Initial fetch
  const { data } = await supabase
    .from('agent_actions')
    .select('*')
    .eq('simulation_id', props.simulationId)
    .order('timestamp', { ascending: true })
    .limit(50)
  
  if (data) {
    actions.value = data
    scrollToBottom()
  }

  subscribeToLogs()
})

onUnmounted(() => {
  if (subscription) {
    supabase.removeChannel(subscription)
  }
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  @apply bg-white/10 rounded-full hover:bg-white/20;
}

.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}
.list-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
