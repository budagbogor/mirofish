<template>
  <div class="space-y-8 animate-in fade-in duration-700">
    <!-- Hero Stats Section -->
    <section class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div v-for="stat in stats" :key="stat.label" 
           class="glass-card glass-card-hover p-6 flex flex-col items-center justify-center space-y-2 group">
        <div :class="`p-3 rounded-2xl bg-${stat.color}-500/10 text-${stat.color}-400 group-hover:scale-110 transition-transform` ">
          <component :is="stat.icon" :size="28" />
        </div>
        <p class="text-3xl font-bold font-outfit">{{ stat.value }}</p>
        <p class="text-sm text-slate-400 font-medium uppercase tracking-wider">{{ stat.label }}</p>
      </div>
    </section>

    <!-- Main Dashboard Body -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left Column: Project Catalog -->
      <section class="lg:col-span-2 space-y-6">
        <div class="flex items-center justify-between px-2">
          <h3 class="text-xl font-semibold flex items-center gap-2">
            <FolderKanban class="text-sky-400" :size="24" />
            Recent Projects
          </h3>
          <button class="text-sm text-sky-400 hover:text-sky-300 font-medium transition-colors">View All</button>
        </div>

        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="i in 4" :key="i" class="h-40 glass-card animate-pulse"></div>
        </div>

        <div v-else-if="projects.length === 0" class="glass-card p-12 text-center space-y-4">
          <div class="p-6 bg-white/5 inline-block rounded-full">
            <LayoutDashboard class="text-slate-600" :size="48" />
          </div>
          <h4 class="text-lg font-medium">No projects found in the cloud</h4>
          <p class="text-slate-400 max-w-xs mx-auto text-sm">Start your architectural journey by creating your first reality simulation.</p>
          <button @click="showNewProjectModal = true" class="aurora-btn">Create New Project</button>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-for="project in projects" :key="project.id" 
               class="glass-card glass-card-hover p-5 space-y-4 cursor-pointer group"
               @click="goToProject(project.project_id)">
            <div class="flex justify-between items-start">
              <div class="p-2 rounded-lg bg-white/5">
                <Globe :size="20" class="text-purple-400" />
              </div>
              <span class="text-[10px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">Synced</span>
            </div>
            <div>
              <h4 class="font-semibold text-lg group-hover:text-sky-400 transition-colors truncate">{{ project.name }}</h4>
              <p class="text-xs text-slate-500 mt-1">ID: {{ project.project_id }}</p>
            </div>
            <div class="flex items-center justify-between pt-4 border-t border-white/5">
              <div class="text-[10px] space-y-1">
                <p class="text-slate-500">Created</p>
                <p class="text-slate-300">{{ formatDate(project.created_at) }}</p>
              </div>
              <ArrowUpRight :size="16" class="text-slate-600 group-hover:text-white group-hover:translate-x-1 group-hover:-translate-y-1 transition-all" />
            </div>
          </div>
        </div>
      </section>

      <!-- Right Column: Quick Start Action -->
      <section class="space-y-6">
        <div class="px-2">
          <h3 class="text-xl font-semibold flex items-center gap-2">
            <Zap class="text-aurora-pink" :size="24" />
            Launch Simulation
          </h3>
        </div>

        <div class="glass-card p-6 space-y-6 border-pink-500/10 bg-gradient-to-br from-pink-500/5 to-transparent">
          <div class="space-y-2">
            <label class="text-xs font-semibold text-slate-400 uppercase tracking-widest">Requirement Prompt</label>
            <textarea 
              v-model="requirement"
              placeholder="Describe the reality you want to simulate..."
              class="w-full h-32 bg-slate-900/50 border border-white/10 rounded-xl p-4 text-sm focus:outline-none focus:border-aurora-pink/50 transition-colors"
            ></textarea>
          </div>

          <div class="space-y-2">
            <label class="text-xs font-semibold text-slate-400 uppercase tracking-widest">Reality Seed (PDF)</label>
            <div @click="triggerFileInput" 
                 class="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-pink-500/30 transition-colors cursor-pointer group">
              <input ref="fileInput" type="file" class="hidden" @change="handleFileSelect" accept=".pdf" />
              <Upload class="mx-auto text-slate-600 group-hover:text-pink-400 transition-colors mb-2" :size="32" />
              <p class="text-xs text-slate-500" v-if="!selectedFile">Drag and drop architecture file or <span class="text-pink-400">browse</span></p>
              <p class="text-xs text-sky-400 font-medium" v-else>{{ selectedFile.name }}</p>
            </div>
          </div>

          <button @click="handleInitialize" :disabled="isLaunching" 
                  class="w-full aurora-btn py-4 flex items-center justify-center gap-2 group disabled:opacity-50">
            <div v-if="isLaunching" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            <Play v-else :size="18" fill="currentColor" />
            <span>{{ isLaunching ? 'Initializing...' : 'Initialize Simulation' }}</span>
          </button>
        </div>

        <!-- System Activity Small Feed -->
        <div class="glass-card p-4 space-y-4">
          <h5 class="text-xs font-bold text-slate-500 uppercase flex items-center gap-2">
            <Layers :size="14" /> Recent Activity
          </h5>
          <div class="space-y-3">
            <div v-for="i in 3" :key="i" class="flex items-center gap-3 text-xs border-l-2 border-white/5 pl-3">
              <div class="w-1.5 h-1.5 rounded-full bg-sky-400"></div>
              <p class="text-slate-400"><span class="text-slate-200">Simulation</span> #AX29 ended</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  FolderKanban, 
  Zap, 
  LayoutDashboard, 
  Globe, 
  ArrowUpRight, 
  Upload, 
  Play,
  Layers,
  Database,
  Search,
  Users
} from 'lucide-vue-next'
import { supabase } from '../supabase'

const router = useRouter()
const projects = ref([])
const loading = ref(true)
const requirement = ref('')
const isLaunching = ref(false)
const selectedFile = ref(null)
const fileInput = ref(null)

const stats = [
  { label: 'Cloud Projects', value: '0', icon: Database, color: 'sky' },
  { label: 'Active Agents', value: '1,280', icon: Users, color: 'purple' },
  { label: 'Total Actions', value: '42.5K', icon: Zap, color: 'pink' }
]

const triggerFileInput = () => fileInput.value?.click()

const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file && file.type === 'application/pdf') {
    selectedFile.value = file
  }
}

const handleInitialize = async () => {
  if (!selectedFile.value || !requirement.value) {
    alert('Please provide both a requirement prompt and a PDF reality seed.')
    return
  }

  isLaunching.value = true
  try {
    const projectId = `proj_${Math.random().toString(36).substr(2, 9)}`
    
    // 1. Create Project Entry in Supabase
    const { error: dbError } = await supabase.from('projects').insert({
      project_id: projectId,
      name: `Simulation: ${requirement.value.substring(0, 20)}...`,
      status: 'initializing',
      metadata: { requirement: requirement.value }
    })
    if (dbError) throw dbError

    // 2. Upload PDF to Storage
    const fileName = `${projectId}/seed.pdf`
    const { error: storageError } = await supabase.storage
      .from('uploads')
      .upload(fileName, selectedFile.value)
    if (storageError) throw storageError
    
    // 3. Navigate to Process View
    router.push({ name: 'Process', params: { projectId } })
  } catch (error) {
    console.error('Initialization failed:', error)
    alert('Failed to initialize cloud project. Check console.')
  } finally {
    isLaunching.value = false
  }
}

const fetchProjects = async () => {
  loading.value = true
  try {
    const { data, error } = await supabase
      .from('projects')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(6)
    
    if (error) throw error
    projects.value = data || []
    stats[0].value = projects.value.length.toString()
  } catch (error) {
    console.error('Error fetching projects:', error)
  } finally {
    loading.value = false
  }
}

const goToProject = (id) => {
  router.push({ name: 'SimulationView', params: { projectId: id } })
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.animate-in {
  animation: fadeIn 0.8s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
