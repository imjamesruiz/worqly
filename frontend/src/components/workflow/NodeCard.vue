<template>
  <div
    :class="[
      'workflow-node',
      'bg-white',
      'border-2',
      'rounded-lg',
      'shadow-lg',
      'min-w-[280px]',
      'relative',
      'transition-all',
      'duration-200',
      'hover:shadow-xl',
      {
        'border-blue-500': selected,
        'border-gray-300': !selected,
        'opacity-50': dragging,
        'cursor-grabbing': dragging,
        'cursor-grab': !dragging
      }
    ]"
    @click="$emit('configure', { nodeId: id })"
  >
    <!-- Node Header -->
    <div class="flex items-center justify-between p-3 border-b border-gray-200">
      <div class="flex items-center space-x-2">
        <div
          :class="[
            'w-3 h-3 rounded-full',
            getNodeTypeColor(data.type)
          ]"
        ></div>
        <span class="text-sm font-medium text-gray-900">{{ data.label }}</span>
      </div>
      
      <div class="flex items-center space-x-1">
        <!-- Status Indicator -->
        <div
          :class="[
            'w-2 h-2 rounded-full',
            getStatusColor(data.status)
          ]"
        ></div>
        
        <!-- Node Actions -->
        <div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            @click.stop="$emit('duplicate', { nodeId: id })"
            class="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            title="Duplicate"
          >
            <Copy class="w-3 h-3" />
          </button>
          <button
            @click.stop="$emit('delete', { nodeId: id })"
            class="p-1 text-gray-400 hover:text-red-600 transition-colors"
            title="Delete"
          >
            <Trash2 class="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>

    <!-- Node Body -->
    <div class="p-3">
      <div class="text-xs text-gray-500 mb-2">
        {{ getNodeTypeDescription(data.type) }}
      </div>
      
      <!-- Node Configuration Preview -->
      <div v-if="data.type === 'trigger'" class="text-xs text-gray-600">
        <div v-if="data.config?.trigger_type" class="flex items-center space-x-1">
          <span class="font-medium">Type:</span>
          <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
            {{ data.config.trigger_type }}
          </span>
        </div>
      </div>
      
      <div v-else-if="data.type === 'action'" class="text-xs text-gray-600">
        <div v-if="data.config?.action_type" class="flex items-center space-x-1">
          <span class="font-medium">Action:</span>
          <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
            {{ data.config.action_type }}
          </span>
        </div>
      </div>
      
      <div v-else-if="data.type === 'condition'" class="text-xs text-gray-600">
        <div v-if="data.config?.condition_type" class="flex items-center space-x-1">
          <span class="font-medium">Logic:</span>
          <span class="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">
            {{ data.config.condition_type }}
          </span>
        </div>
      </div>
    </div>

    <!-- Input Ports -->
    <div
      v-if="data.inputs && data.inputs.length > 0"
      class="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-2"
    >
      <div
        v-for="input in data.inputs"
        :key="input.id"
        :data-port-id="input.id"
        :data-port-direction="'input'"
        :class="[
          'workflow-handle',
          'workflow-handle-input',
          'border-blue-500',
          'hover:bg-blue-500',
          'hover:border-blue-600',
          {
            'bg-blue-500': isConnecting && canConnectTo(input),
            'bg-white': !isConnecting || !canConnectTo(input)
          }
        ]"
        @mousedown.stop="handlePortMouseDown($event, input, 'input')"
        @mouseup.stop="handlePortMouseUp($event, input, 'input')"
        :title="input.label"
      ></div>
    </div>

    <!-- Output Ports -->
    <div
      v-if="data.outputs && data.outputs.length > 0"
      class="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-2"
    >
      <div
        v-for="output in data.outputs"
        :key="output.id"
        :data-port-id="output.id"
        :data-port-direction="'output'"
        :class="[
          'workflow-handle',
          'workflow-handle-output',
          'border-green-500',
          'hover:bg-green-500',
          'hover:border-green-600',
          {
            'bg-green-500': isConnecting && canConnectFrom(output),
            'bg-white': !isConnecting || !canConnectFrom(output)
          }
        ]"
        @mousedown.stop="handlePortMouseDown($event, output, 'output')"
        @mouseup.stop="handlePortMouseUp($event, output, 'output')"
        :title="output.label"
      ></div>
    </div>

    <!-- Special handling for condition nodes with multiple outputs -->
    <div
      v-if="data.type === 'condition' && data.outputs && data.outputs.length > 1"
      class="absolute right-0 transform -translate-y-1/2 translate-x-2"
      :style="{ top: '50%' }"
    >
      <div
        v-for="(output, index) in data.outputs"
        :key="output.id"
        :data-port-id="output.id"
        :data-port-direction="'output'"
        :class="[
          'workflow-handle',
          'workflow-handle-output',
          'border-green-500',
          'hover:bg-green-500',
          'hover:border-green-600',
          {
            'bg-green-500': isConnecting && canConnectFrom(output),
            'bg-white': !isConnecting || !canConnectFrom(output)
          }
        ]"
        :style="{
          top: `${50 + (index - (data.outputs.length - 1) / 2) * 20}%`,
          position: 'absolute'
        }"
        @mousedown.stop="handlePortMouseDown($event, output, 'output')"
        @mouseup.stop="handlePortMouseUp($event, output, 'output')"
        :title="output.label"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { Copy, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  data: {
    type: Object,
    required: true
  },
  selected: {
    type: Boolean,
    default: false
  },
  dragging: {
    type: Boolean,
    default: false
  },
  isConnecting: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'start-connection',
  'configure',
  'duplicate',
  'delete'
])

const getNodeTypeColor = (type) => {
  const colors = {
    trigger: 'bg-green-500',
    action: 'bg-blue-500',
    condition: 'bg-yellow-500',
    transformer: 'bg-purple-500',
    webhook: 'bg-red-500'
  }
  return colors[type] || 'bg-gray-500'
}

const getStatusColor = (status) => {
  const colors = {
    idle: 'bg-gray-400',
    running: 'bg-blue-500',
    success: 'bg-green-500',
    error: 'bg-red-500',
    completed: 'bg-green-500',
    failed: 'bg-red-500'
  }
  return colors[status] || 'bg-gray-400'
}

const getNodeTypeDescription = (type) => {
  const descriptions = {
    trigger: 'Starts the workflow',
    action: 'Performs an action',
    condition: 'Makes decisions',
    transformer: 'Transforms data',
    webhook: 'External trigger'
  }
  return descriptions[type] || 'Workflow node'
}

const canConnectTo = (input) => {
  // For now, allow all connections
  // In a real implementation, you'd check port types, etc.
  return true
}

const canConnectFrom = (output) => {
  // For now, allow all connections
  // In a real implementation, you'd check port types, etc.
  return true
}

const handlePortMouseDown = (event, port, direction) => {
  if (direction === 'output') {
    emit('start-connection', {
      nodeId: props.id,
      portId: port.id,
      direction,
      port
    })
  }
}

const handlePortMouseUp = (event, port, direction) => {
  // This will be handled by the parent component
  // The parent listens for mouseup events on the canvas
}
</script>

<style scoped>
.workflow-node {
  min-height: 120px;
}

.workflow-handle {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  z-index: 10;
}

.workflow-handle:hover {
  transform: scale(1.2);
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.1);
}

.workflow-handle-input {
  left: -8px;
}

.workflow-handle-output {
  right: -8px;
}

.workflow-node:hover .opacity-0 {
  opacity: 1;
}
</style>