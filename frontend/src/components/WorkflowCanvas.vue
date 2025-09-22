<template>
  <div class="workflow-canvas-container">
    <!-- Toolbar -->
    <div class="workflow-toolbar">
      <div class="toolbar-left">
        <input
          v-model="workflowName"
          class="workflow-name-input"
          placeholder="Workflow name"
        />
        <button @click="saveWorkflow" class="btn btn-primary">
          <Save class="w-4 h-4 mr-2" />
          Save
        </button>
        <button @click="executeWorkflow" :disabled="isExecuting" class="btn btn-success">
          <Play v-if="!isExecuting" class="w-4 h-4 mr-2" />
          <Pause v-else class="w-4 h-4 mr-2" />
          {{ isExecuting ? 'Running...' : 'Execute' }}
        </button>
        <button @click="testWorkflow" :disabled="isExecuting" class="btn btn-warning">
          <TestTube class="w-4 h-4 mr-2" />
          Test
        </button>
      </div>
      
      <div class="toolbar-right">
        <div class="execution-status">
          <span v-if="executionStatus === 'completed'" class="status-badge success">
            <CheckCircle class="w-4 h-4 mr-1" />
            Completed
          </span>
          <span v-if="executionStatus === 'error'" class="status-badge error">
            <AlertCircle class="w-4 h-4 mr-1" />
            Error
          </span>
        </div>
        
        <div class="zoom-controls">
          <button @click="zoomIn" class="btn btn-sm btn-outline">
            <ZoomIn class="w-4 h-4" />
          </button>
          <button @click="zoomOut" class="btn btn-sm btn-outline">
            <ZoomOut class="w-4 h-4" />
          </button>
          <button @click="resetZoom" class="btn btn-sm btn-outline">
            <RotateCcw class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Main Canvas Area -->
    <div class="canvas-main">
      <!-- Node Palette -->
      <NodeSidebar @node-drag="handleNodeDrag" />
      
      <!-- Joint.js Canvas -->
      <div 
        ref="canvasContainer" 
        class="joint-canvas"
        @drop="handleDrop"
        @dragover="handleDragOver"
        @dragenter="handleDragEnter"
        @dragleave="handleDragLeave"
      ></div>
      
      <!-- Properties Panel -->
      <NodeConfigPanel 
        v-if="selectedNode"
        :node="selectedNode"
        @update-node="updateNode"
        @close="selectedNode = null"
      />
    </div>

    <!-- Execution Logs Panel -->
    <div v-if="showLogs" class="logs-panel">
      <div class="logs-header">
        <h3>Execution Logs</h3>
        <button @click="showLogs = false" class="btn btn-sm btn-outline">
          <X class="w-4 h-4" />
        </button>
      </div>
      <div class="logs-content">
        <div 
          v-for="log in executionLogs" 
          :key="log.id"
          class="log-entry"
          :class="log.status"
        >
          <div class="log-header">
            <span class="log-node">{{ log.node_name }}</span>
            <span class="log-status">{{ log.status }}</span>
            <span class="log-time">{{ log.execution_time_ms }}ms</span>
          </div>
          <div v-if="log.error_message" class="log-error">
            {{ log.error_message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useWorkflowsStore } from '@/stores/workflows'
import { useToast } from 'vue-toastification'
import joint from 'jointjs'
import NodeSidebar from './NodeSidebar.vue'
import NodeConfigPanel from './NodeConfigPanel.vue'
import { 
  Save, Play, Pause, TestTube, CheckCircle, AlertCircle, 
  ZoomIn, ZoomOut, RotateCcw, X 
} from 'lucide-vue-next'

const props = defineProps({
  workflowId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['workflow-saved', 'workflow-executed'])

// Stores and services
const workflowsStore = useWorkflowsStore()
const toast = useToast()

// Reactive state
const workflowName = ref('New Workflow')
const isExecuting = ref(false)
const executionStatus = ref('idle')
const selectedNode = ref(null)
const showLogs = ref(false)
const executionLogs = ref([])

// Joint.js references
const canvasContainer = ref(null)
let graph = null
let paper = null

// Initialize Joint.js canvas
const initializeCanvas = () => {
  if (!canvasContainer.value) return

  // Create graph and paper
  graph = new joint.dia.Graph()
  paper = new joint.dia.Paper({
    el: canvasContainer.value,
    model: graph,
    width: '100%',
    height: '100%',
    gridSize: 20,
    drawGrid: true,
    background: {
      color: '#f8f9fa'
    },
    defaultConnector: {
      name: 'rounded'
    },
    defaultRouter: {
      name: 'orthogonal'
    },
    interactive: {
      linkMove: false,
      elementMove: true,
      arrowheadMove: false,
      vertexMove: false,
      vertexAdd: false,
      vertexRemove: false,
      useLinkTools: true
    }
  })

  // Handle element selection
  paper.on('element:pointerclick', (elementView) => {
    const element = elementView.model
    selectedNode.value = {
      id: element.id,
      type: element.get('type'),
      label: element.get('attrs/label/text'),
      config: element.get('config') || {},
      position: element.position()
    }
  })

  // Handle element movement
  paper.on('element:pointerup', (elementView) => {
    const element = elementView.model
    updateNodePosition(element.id, element.position())
  })

  // Handle link creation
  paper.on('link:connect', (linkView) => {
    const link = linkView.model
    createConnection(link)
  })

  // Handle link deletion
  paper.on('link:pointerclick', (linkView, evt) => {
    if (evt.ctrlKey || evt.metaKey) {
      linkView.model.remove()
    }
  })

  // Handle canvas click (deselect)
  paper.on('blank:pointerclick', () => {
    selectedNode.value = null
  })
}

// Load workflow data
const loadWorkflow = async () => {
  try {
    const workflow = await workflowsStore.fetchWorkflow(props.workflowId)
    workflowName.value = workflow.name || 'New Workflow'
    
    // Clear existing elements
    graph.clear()
    
    // Load nodes
    if (workflow.nodes) {
      workflow.nodes.forEach(node => {
        createJointNode(node)
      })
    }
    
    // Load connections
    if (workflow.connections) {
      workflow.connections.forEach(connection => {
        createJointLink(connection)
      })
    }
  } catch (error) {
    console.error('Failed to load workflow:', error)
    toast.error('Failed to load workflow')
  }
}

// Create Joint.js node
const createJointNode = (nodeData) => {
  const nodeType = getNodeType(nodeData.node_type)
  const node = new nodeType({
    id: nodeData.node_id,
    position: { x: nodeData.position_x, y: nodeData.position_y },
    size: { width: 200, height: 80 },
    attrs: {
      body: {
        fill: getNodeColor(nodeData.node_type),
        stroke: '#333',
        strokeWidth: 2,
        rx: 5,
        ry: 5
      },
      label: {
        text: nodeData.name,
        fontSize: 12,
        fontWeight: 'bold',
        fill: '#333'
      },
      icon: {
        text: getNodeIcon(nodeData.node_type),
        fontSize: 16,
        fill: '#fff'
      }
    },
    config: nodeData.config || {},
    type: nodeData.node_type
  })
  
  graph.addCell(node)
  return node
}

// Create Joint.js link
const createJointLink = (connectionData) => {
  const link = new joint.shapes.standard.Link({
    id: connectionData.connection_id,
    source: { id: connectionData.source_node_id },
    target: { id: connectionData.target_node_id },
    attrs: {
      line: {
        stroke: '#666',
        strokeWidth: 2,
        targetMarker: {
          'type': 'path',
          'd': 'M 10 -5 0 0 10 5 z'
        }
      }
    },
    connectionData
  })
  
  graph.addCell(link)
  return link
}

// Get node type class
const getNodeType = (nodeType) => {
  const nodeTypes = {
    'trigger': joint.shapes.standard.Rectangle,
    'action': joint.shapes.standard.Rectangle,
    'condition': joint.shapes.standard.Rectangle,
    'transformer': joint.shapes.standard.Rectangle,
    'webhook': joint.shapes.standard.Rectangle,
    'delay': joint.shapes.standard.Rectangle,
    'loop': joint.shapes.standard.Rectangle
  }
  return nodeTypes[nodeType] || joint.shapes.standard.Rectangle
}

// Get node color
const getNodeColor = (nodeType) => {
  const colors = {
    'trigger': '#10b981',
    'action': '#3b82f6',
    'condition': '#8b5cf6',
    'transformer': '#f59e0b',
    'webhook': '#ef4444',
    'delay': '#6b7280',
    'loop': '#ec4899'
  }
  return colors[nodeType] || '#6b7280'
}

// Get node icon
const getNodeIcon = (nodeType) => {
  const icons = {
    'trigger': '⚡',
    'action': '⚙️',
    'condition': '❓',
    'transformer': '🔄',
    'webhook': '🔗',
    'delay': '⏱️',
    'loop': '🔄'
  }
  return icons[nodeType] || '📦'
}

// Handle node drag from palette
const handleNodeDrag = (nodeData) => {
  // This will be handled by the drop event
}

// Handle drop from palette
const handleDrop = async (event) => {
  event.preventDefault()
  
  try {
    const nodeData = JSON.parse(event.dataTransfer.getData('application/json'))
    const rect = canvasContainer.value.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    
    // Create new node
    const newNode = {
      node_id: `node_${Date.now()}`,
      node_type: nodeData.type,
      name: nodeData.label,
      position_x: x,
      position_y: y,
      config: {},
      workflow_id: parseInt(props.workflowId)
    }
    
    // Save to backend
    const savedNode = await workflowsStore.createNode(props.workflowId, newNode)
    
    // Create Joint.js node
    createJointNode(savedNode)
    
    toast.success('Node added successfully')
  } catch (error) {
    console.error('Failed to add node:', error)
    toast.error('Failed to add node')
  }
}

// Handle drag over
const handleDragOver = (event) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'copy'
}

// Handle drag enter
const handleDragEnter = (event) => {
  event.preventDefault()
}

// Handle drag leave
const handleDragLeave = (event) => {
  event.preventDefault()
}

// Update node position
const updateNodePosition = async (nodeId, position) => {
  try {
    await workflowsStore.updateNode(props.workflowId, nodeId, {
      position_x: position.x,
      position_y: position.y
    })
  } catch (error) {
    console.error('Failed to update node position:', error)
  }
}

// Create connection
const createConnection = async (link) => {
  try {
    const connectionData = {
      connection_id: link.id,
      source_node_id: link.getSourceElement().id,
      target_node_id: link.getTargetElement().id,
      workflow_id: parseInt(props.workflowId)
    }
    
    await workflowsStore.createConnection(props.workflowId, connectionData)
    toast.success('Connection created')
  } catch (error) {
    console.error('Failed to create connection:', error)
    toast.error('Failed to create connection')
    link.remove() // Remove the link if creation failed
  }
}

// Update node
const updateNode = async (nodeId, updates) => {
  try {
    await workflowsStore.updateNode(props.workflowId, nodeId, updates)
    
    // Update Joint.js element
    const element = graph.getCell(nodeId)
    if (element) {
      element.set('attrs/label/text', updates.name || element.get('attrs/label/text'))
      element.set('config', { ...element.get('config'), ...updates.config })
    }
    
    toast.success('Node updated')
  } catch (error) {
    console.error('Failed to update node:', error)
    toast.error('Failed to update node')
  }
}

// Save workflow
const saveWorkflow = async () => {
  try {
    await workflowsStore.updateWorkflow(props.workflowId, {
      name: workflowName.value
    })
    toast.success('Workflow saved')
    emit('workflow-saved')
  } catch (error) {
    console.error('Failed to save workflow:', error)
    toast.error('Failed to save workflow')
  }
}

// Execute workflow
const executeWorkflow = async () => {
  try {
    isExecuting.value = true
    executionStatus.value = 'running'
    
    const result = await workflowsStore.executeWorkflow(props.workflowId)
    
    executionStatus.value = result.success ? 'completed' : 'error'
    executionLogs.value = result.logs || []
    showLogs.value = true
    
    toast.success('Workflow executed successfully')
    emit('workflow-executed', result)
  } catch (error) {
    console.error('Failed to execute workflow:', error)
    executionStatus.value = 'error'
    toast.error('Failed to execute workflow')
  } finally {
    isExecuting.value = false
  }
}

// Test workflow
const testWorkflow = async () => {
  try {
    isExecuting.value = true
    executionStatus.value = 'running'
    
    const result = await workflowsStore.testWorkflow(props.workflowId)
    
    executionStatus.value = result.success ? 'completed' : 'error'
    executionLogs.value = result.logs || []
    showLogs.value = true
    
    toast.success('Workflow test completed')
  } catch (error) {
    console.error('Failed to test workflow:', error)
    executionStatus.value = 'error'
    toast.error('Failed to test workflow')
  } finally {
    isExecuting.value = false
  }
}

// Zoom controls
const zoomIn = () => {
  paper.scale(paper.scale().sx * 1.2, paper.scale().sy * 1.2)
}

const zoomOut = () => {
  paper.scale(paper.scale().sx * 0.8, paper.scale().sy * 0.8)
}

const resetZoom = () => {
  paper.scale(1, 1)
  paper.center()
}

// Lifecycle
onMounted(async () => {
  await nextTick()
  initializeCanvas()
  await loadWorkflow()
})

onUnmounted(() => {
  if (paper) {
    paper.remove()
  }
  if (graph) {
    graph.clear()
  }
})
</script>

<style scoped>
.workflow-canvas-container {
  @apply h-full flex flex-col bg-gray-50;
}

.workflow-toolbar {
  @apply flex items-center justify-between p-4 bg-white border-b border-gray-200;
}

.toolbar-left {
  @apply flex items-center space-x-3;
}

.toolbar-right {
  @apply flex items-center space-x-3;
}

.workflow-name-input {
  @apply px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent;
}

.btn {
  @apply px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2;
}

.btn-primary {
  @apply bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500;
}

.btn-success {
  @apply bg-green-600 text-white hover:bg-green-700 focus:ring-green-500;
}

.btn-warning {
  @apply bg-yellow-600 text-white hover:bg-yellow-700 focus:ring-yellow-500;
}

.btn-outline {
  @apply border border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-gray-500;
}

.btn-sm {
  @apply px-2 py-1 text-sm;
}

.status-badge {
  @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium;
}

.status-badge.success {
  @apply bg-green-100 text-green-800;
}

.status-badge.error {
  @apply bg-red-100 text-red-800;
}

.zoom-controls {
  @apply flex items-center space-x-1;
}

.canvas-main {
  @apply flex-1 flex;
}

.joint-canvas {
  @apply flex-1;
}

.logs-panel {
  @apply w-80 bg-white border-l border-gray-200 flex flex-col;
}

.logs-header {
  @apply flex items-center justify-between p-4 border-b border-gray-200;
}

.logs-content {
  @apply flex-1 overflow-y-auto p-4;
}

.log-entry {
  @apply mb-3 p-3 rounded-lg border;
}

.log-entry.completed {
  @apply bg-green-50 border-green-200;
}

.log-entry.failed {
  @apply bg-red-50 border-red-200;
}

.log-entry.running {
  @apply bg-yellow-50 border-yellow-200;
}

.log-header {
  @apply flex items-center justify-between text-sm;
}

.log-node {
  @apply font-medium;
}

.log-status {
  @apply px-2 py-1 rounded text-xs font-medium;
}

.log-time {
  @apply text-gray-500;
}

.log-error {
  @apply mt-2 text-sm text-red-600;
}
</style>
