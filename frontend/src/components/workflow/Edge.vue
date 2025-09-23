<template>
  <g>
    <!-- Connection Path -->
    <path
      :d="pathData"
      :stroke="strokeColor"
      :stroke-width="strokeWidth"
      :stroke-dasharray="strokeDasharray"
      fill="none"
      :marker-end="markerEnd"
      class="workflow-edge"
      :class="{
        'workflow-edge-selected': selected,
        'workflow-edge-error': data.type === 'error'
      }"
      @click="handleEdgeClick"
      @contextmenu="handleContextMenu"
    />
    
    <!-- Edge Label -->
    <text
      v-if="data.label"
      :x="labelPosition.x"
      :y="labelPosition.y"
      class="workflow-edge-label"
      text-anchor="middle"
      dominant-baseline="middle"
      @click="handleLabelClick"
    >
      {{ data.label }}
    </text>
    
    <!-- Error Message -->
    <text
      v-if="data.type === 'error' && data.errorMessage"
      :x="labelPosition.x"
      :y="labelPosition.y + 15"
      class="workflow-edge-error-text"
      text-anchor="middle"
      dominant-baseline="middle"
    >
      {{ data.errorMessage }}
    </text>
  </g>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  id: {
    type: String,
    required: true
  },
  sourceX: {
    type: Number,
    required: true
  },
  sourceY: {
    type: Number,
    required: true
  },
  targetX: {
    type: Number,
    required: true
  },
  targetY: {
    type: Number,
    required: true
  },
  data: {
    type: Object,
    default: () => ({})
  },
  selected: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'edge-click',
  'edge-context-menu',
  'edge-label-edit',
  'edge-rename',
  'edge-delete'
])

const pathData = computed(() => {
  const { sourceX, sourceY, targetX, targetY } = props
  
  // Create a smooth curved path
  const dx = targetX - sourceX
  const dy = targetY - sourceY
  
  // Control points for the curve
  const cp1x = sourceX + dx * 0.5
  const cp1y = sourceY
  const cp2x = targetX - dx * 0.5
  const cp2y = targetY
  
  return `M ${sourceX} ${sourceY} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${targetX} ${targetY}`
})

const strokeColor = computed(() => {
  if (props.data.type === 'error') return '#ef4444'
  if (props.selected) return '#3b82f6'
  return '#6b7280'
})

const strokeWidth = computed(() => {
  if (props.selected) return 3
  return 2
})

const strokeDasharray = computed(() => {
  if (props.data.type === 'error') return '5,5'
  return 'none'
})

const markerEnd = computed(() => {
  if (props.data.type === 'error') return 'url(#arrowhead-error)'
  if (props.selected) return 'url(#arrowhead-selected)'
  return 'url(#arrowhead)'
})

const labelPosition = computed(() => {
  const { sourceX, sourceY, targetX, targetY } = props
  return {
    x: (sourceX + targetX) / 2,
    y: (sourceY + targetY) / 2
  }
})

const handleEdgeClick = (event) => {
  event.stopPropagation()
  emit('edge-click', { edgeId: props.id })
}

const handleContextMenu = (event) => {
  event.preventDefault()
  event.stopPropagation()
  emit('edge-context-menu', { edgeId: props.id })
}

const handleLabelClick = (event) => {
  event.stopPropagation()
  emit('edge-label-edit', { edgeId: props.id, label: props.data.label })
}
</script>

<style scoped>
.workflow-edge {
  cursor: pointer;
  transition: all 0.2s ease;
}

.workflow-edge:hover {
  stroke-width: 3;
}

.workflow-edge-selected {
  stroke-width: 3;
  filter: drop-shadow(0 0 3px rgba(59, 130, 246, 0.5));
}

.workflow-edge-error {
  stroke-width: 2;
  animation: dash 1s linear infinite;
}

.workflow-edge-label {
  font-size: 12px;
  fill: #374151;
  font-weight: 500;
  pointer-events: none;
}

.workflow-edge-error-text {
  font-size: 10px;
  fill: #ef4444;
  font-weight: 500;
  pointer-events: none;
}

@keyframes dash {
  to {
    stroke-dashoffset: -10;
  }
}
</style>