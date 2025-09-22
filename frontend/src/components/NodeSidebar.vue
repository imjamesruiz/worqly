<template>
  <div class="node-sidebar">
    <div class="sidebar-header">
      <h3 class="sidebar-title">Node Palette</h3>
    </div>
    
    <div class="sidebar-content">
      <!-- Triggers Section -->
      <div class="node-section">
        <div class="section-header">
          <div class="section-icon trigger-icon">⚡</div>
          <span class="section-title">Triggers</span>
        </div>
        <div class="node-list">
          <div
            v-for="node in triggerNodes"
            :key="node.type"
            class="node-item trigger-node"
            draggable="true"
            @dragstart="onDragStart($event, node)"
          >
            <div class="node-icon">{{ node.icon }}</div>
            <div class="node-info">
              <div class="node-label">{{ node.label }}</div>
              <div class="node-description">{{ node.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Actions Section -->
      <div class="node-section">
        <div class="section-header">
          <div class="section-icon action-icon">⚙️</div>
          <span class="section-title">Actions</span>
        </div>
        <div class="node-list">
          <div
            v-for="node in actionNodes"
            :key="node.type"
            class="node-item action-node"
            draggable="true"
            @dragstart="onDragStart($event, node)"
          >
            <div class="node-icon">{{ node.icon }}</div>
            <div class="node-info">
              <div class="node-label">{{ node.label }}</div>
              <div class="node-description">{{ node.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Logic Section -->
      <div class="node-section">
        <div class="section-header">
          <div class="section-icon logic-icon">🧠</div>
          <span class="section-title">Logic</span>
        </div>
        <div class="node-list">
          <div
            v-for="node in logicNodes"
            :key="node.type"
            class="node-item logic-node"
            draggable="true"
            @dragstart="onDragStart($event, node)"
          >
            <div class="node-icon">{{ node.icon }}</div>
            <div class="node-info">
              <div class="node-label">{{ node.label }}</div>
              <div class="node-description">{{ node.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Data Section -->
      <div class="node-section">
        <div class="section-header">
          <div class="section-icon data-icon">📊</div>
          <span class="section-title">Data</span>
        </div>
        <div class="node-list">
          <div
            v-for="node in dataNodes"
            :key="node.type"
            class="node-item data-node"
            draggable="true"
            @dragstart="onDragStart($event, node)"
          >
            <div class="node-icon">{{ node.icon }}</div>
            <div class="node-info">
              <div class="node-label">{{ node.label }}</div>
              <div class="node-description">{{ node.description }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['node-drag'])

const triggerNodes = ref([
  {
    type: 'gmail_trigger',
    label: 'Gmail Trigger',
    description: 'Trigger on new email',
    icon: '📧'
  },
  {
    type: 'webhook_trigger',
    label: 'Webhook',
    description: 'Trigger on HTTP request',
    icon: '🔗'
  },
  {
    type: 'schedule_trigger',
    label: 'Schedule',
    description: 'Trigger on schedule',
    icon: '⏰'
  },
  {
    type: 'slack_trigger',
    label: 'Slack Trigger',
    description: 'Trigger on Slack message',
    icon: '💬'
  }
])

const actionNodes = ref([
  {
    type: 'gmail_action',
    label: 'Send Email',
    description: 'Send email via Gmail',
    icon: '📤'
  },
  {
    type: 'slack_action',
    label: 'Slack Message',
    description: 'Send Slack message',
    icon: '💬'
  },
  {
    type: 'sheets_action',
    label: 'Google Sheets',
    description: 'Update spreadsheet',
    icon: '📊'
  },
  {
    type: 'http_request',
    label: 'HTTP Request',
    description: 'Make HTTP request',
    icon: '🌐'
  },
  {
    type: 'delay_action',
    label: 'Delay',
    description: 'Wait for specified time',
    icon: '⏱️'
  }
])

const logicNodes = ref([
  {
    type: 'condition',
    label: 'Condition',
    description: 'If/else logic',
    icon: '❓'
  },
  {
    type: 'transformer',
    label: 'Data Transformer',
    description: 'Transform data',
    icon: '🔄'
  },
  {
    type: 'filter',
    label: 'Filter',
    description: 'Filter data',
    icon: '🔍'
  },
  {
    type: 'loop',
    label: 'Loop',
    description: 'Repeat actions',
    icon: '🔄'
  }
])

const dataNodes = ref([
  {
    type: 'variable',
    label: 'Variable',
    description: 'Store data',
    icon: '📦'
  },
  {
    type: 'json_parser',
    label: 'JSON Parser',
    description: 'Parse JSON data',
    icon: '📋'
  },
  {
    type: 'csv_parser',
    label: 'CSV Parser',
    description: 'Parse CSV data',
    icon: '📄'
  }
])

const onDragStart = (event, node) => {
  event.dataTransfer.setData('application/json', JSON.stringify(node))
  event.dataTransfer.effectAllowed = 'copy'
  emit('node-drag', node)
}
</script>

<style scoped>
.node-sidebar {
  @apply w-64 bg-white border-r border-gray-200 flex flex-col h-full;
}

.sidebar-header {
  @apply p-4 border-b border-gray-200;
}

.sidebar-title {
  @apply text-lg font-semibold text-gray-900;
}

.sidebar-content {
  @apply flex-1 overflow-y-auto p-4 space-y-6;
}

.node-section {
  @apply space-y-3;
}

.section-header {
  @apply flex items-center space-x-2 mb-3;
}

.section-icon {
  @apply w-5 h-5 flex items-center justify-center text-sm;
}

.trigger-icon {
  @apply text-green-600;
}

.action-icon {
  @apply text-blue-600;
}

.logic-icon {
  @apply text-purple-600;
}

.data-icon {
  @apply text-orange-600;
}

.section-title {
  @apply text-sm font-medium text-gray-700;
}

.node-list {
  @apply space-y-2;
}

.node-item {
  @apply p-3 border border-gray-200 rounded-lg cursor-move hover:bg-gray-50 transition-colors;
}

.node-item:hover {
  @apply border-gray-300 shadow-sm;
}

.trigger-node {
  @apply border-l-4 border-l-green-500;
}

.action-node {
  @apply border-l-4 border-l-blue-500;
}

.logic-node {
  @apply border-l-4 border-l-purple-500;
}

.data-node {
  @apply border-l-4 border-l-orange-500;
}

.node-item {
  @apply flex items-start space-x-3;
}

.node-icon {
  @apply w-6 h-6 flex items-center justify-center text-lg flex-shrink-0;
}

.node-info {
  @apply flex-1 min-w-0;
}

.node-label {
  @apply text-sm font-medium text-gray-900;
}

.node-description {
  @apply text-xs text-gray-500 mt-1;
}
</style>
