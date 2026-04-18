<template>
  <div class="h-full flex flex-col gap-6 animate-in fade-in zoom-in-95 duration-500">
    <div class="flex flex-col lg:flex-row gap-6 h-[calc(100vh-180px)]">
      <!-- Left: Graph Visualization (Space Architecture) -->
      <div class="lg:w-3/5 h-full relative group">
        <div class="absolute -inset-1 bg-gradient-to-r from-sky-500 to-purple-600 rounded-3xl blur opacity-20 group-hover:opacity-30 transition duration-1000"></div>
        <div class="relative h-full glass-card overflow-hidden">
          <GraphPanel 
            :graphData="graphData"
            :loading="graphLoading"
            :isSimulating="isRunning"
            @refresh="loadGraph"
          />
          
          <!-- Graph Overlays -->
          <div class="absolute bottom-6 left-6 p-4 glass-card bg-slate-900/80 backdrop-blur-xl border-white/5 pointer-events-none">
            <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-1">Entity Context</p>
            <div class="flex items-center gap-4">
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-sky-400"></span>
                <span class="text-xs text-slate-300">Agents</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-purple-400"></span>
                <span class="text-xs text-slate-300">Concepts</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Real-time Live Engine Feed -->
      <div class="lg:w-2/5 h-full">
        <LiveSimulation 
          :simulationId="simulationId"
          :status="status"
          @stop="handleStop"
          @next="handleNext"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import LiveSimulation from '../components/simulation/LiveSimulation.vue'
import { getGraphData } from '../api/graph'
import { supabase } from '../supabase'

const props = defineProps({
  simulationId: { type: String, required: true }
})

const router = useRouter()
const graphData = ref(null)
const graphLoading = ref(true)
const isRunning = ref(true)
const status = ref('running')

const loadGraph = async () => {
  // Logic to load graph from project linked to this simulation
  try {
    const { data: sim } = await supabase
      .from('simulations')
      .select('project_id')
      .eq('simulation_id', props.simulationId)
      .single()
    
    if (sim?.project_id) {
      const { data: proj } = await supabase
        .from('projects')
        .select('graph_id')
        .eq('project_id', sim.project_id)
        .single()
      
      if (proj?.graph_id) {
        const res = await getGraphData(proj.graph_id)
        if (res.success) {
          graphData.value = res.data
        }
      }
    }
  } catch (err) {
    console.error('Failed to load graph:', err)
  } finally {
    graphLoading.value = false
  }
}

const handleStop = async () => {
  if (confirm('Are you sure you want to terminate this architectural simulation?')) {
    isRunning.value = false
    status.value = 'stopped'
    // Call backend API to stop the actual process
    try {
      await fetch(`${import.meta.env.VITE_API_BASE_URL}/api/simulation/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulation_id: props.simulationId })
      })
    } catch (e) {}
  }
}

const handleNext = () => {
  router.push({ name: 'Report', params: { reportId: props.simulationId } })
}

onMounted(() => {
  loadGraph()
  
  // Also listen to simulation status changes in real-time
  const statusSub = supabase
    .channel(`sim-status-${props.simulationId}`)
    .on(
      'postgres_changes',
      { event: 'UPDATE', schema: 'public', table: 'simulations', filter: `simulation_id=eq.${props.simulationId}` },
      (payload) => {
        status.value = payload.new.status
        if (status.value === 'completed' || status.value === 'failed') {
          isRunning.value = false
        }
      }
    )
    .subscribe()
})
</script>

<style scoped>
.animate-in {
  animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
