<template>
  <div class="node-config-panel">
    <div class="panel-header">
      <h3 class="panel-title">Node Configuration</h3>
      <button @click="$emit('close')" class="close-btn">
        <X class="w-4 h-4" />
      </button>
    </div>
    
    <div class="panel-content">
      <!-- Basic Info -->
      <div class="config-section">
        <h4 class="section-title">Basic Information</h4>
        
        <div class="form-group">
          <label class="form-label">Name</label>
          <input
            v-model="localNode.name"
            class="form-input"
            placeholder="Node name"
            @input="updateNode"
          />
        </div>
        
        <div class="form-group">
          <label class="form-label">Type</label>
          <div class="type-badge">
            {{ localNode.type }}
          </div>
        </div>
      </div>

      <!-- Node-specific Configuration -->
      <div class="config-section">
        <h4 class="section-title">Configuration</h4>
        
        <!-- Gmail Trigger -->
        <div v-if="isGmailTrigger" class="config-fields">
          <div class="form-group">
            <label class="form-label">Trigger Type</label>
            <select v-model="localNode.config.trigger_type" class="form-select" @change="updateNode">
              <option value="new_email">New Email</option>
              <option value="email_received">Email Received</option>
              <option value="email_sent">Email Sent</option>
            </select>
          </div>
          
          <div class="form-group">
            <label class="form-label">Label</label>
            <select v-model="localNode.config.label" class="form-select" @change="updateNode">
              <option value="INBOX">Inbox</option>
              <option value="SENT">Sent</option>
              <option value="DRAFT">Draft</option>
              <option value="SPAM">Spam</option>
            </select>
          </div>
          
          <div class="form-group">
            <label class="form-label">From Address (optional)</label>
            <input
              v-model="localNode.config.from_address"
              class="form-input"
              placeholder="sender@example.com"
              @input="updateNode"
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">Subject Contains (optional)</label>
            <input
              v-model="localNode.config.subject_contains"
              class="form-input"
              placeholder="keyword"
              @input="updateNode"
            />
          </div>
        </div>

        <!-- Gmail Action -->
        <div v-else-if="isGmailAction" class="config-fields">
          <div class="form-group">
            <label class="form-label">Action Type</label>
            <select v-model="localNode.config.action_type" class="form-select" @change="updateNode">
              <option value="send_email">Send Email</option>
              <option value="reply_email">Reply to Email</option>
              <option value="forward_email">Forward Email</option>
            </select>
          </div>
          
          <div class="form-group">
            <label class="form-label">To</label>
            <input
              v-model="localNode.config.to"
              class="form-input"
              placeholder="recipient@example.com"
              @input="updateNode"
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">Subject</label>
            <input
              v-model="localNode.config.subject"
              class="form-input"
              placeholder="Email subject"
              @input="updateNode"
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">Body</label>
            <textarea
              v-model="localNode.config.body"
              class="form-textarea"
              placeholder="Email body"
              rows="4"
              @input="updateNode"
            ></textarea>
          </div>
        </div>

        <!-- Slack Action -->
        <div v-else-if="isSlackAction" class="config-fields">
          <div class="form-group">
            <label class="form-label">Action Type</label>
            <select v-model="localNode.config.action_type" class="form-select" @change="updateNode">
              <option value="send_message">Send Message</option>
              <option value="update_message">Update Message</option>
              <option value="delete_message">Delete Message</option>
            </select>
          </div>
          
          <div class="form-group">
            <label class="form-label">Channel</label>
            <input
              v-model="localNode.config.channel"
              class="form-input"
              placeholder="#general or @username"
              @input="updateNode"
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">Message</label>
            <textarea
              v-model="localNode.config.text"
              class="form-textarea"
              placeholder="Message text"
              rows="4"
              @input="updateNode"
            ></textarea>
          </div>
        </div>

        <!-- Webhook Trigger -->
        <div v-else-if="isWebhookTrigger" class="config-fields">
          <div class="form-group">
            <label class="form-label">Webhook URL</label>
            <div class="input-group">
              <input
                v-model="webhookUrl"
                class="form-input"
                readonly
                :value="`${baseUrl}/webhooks/${localNode.id}`"
              />
              <button @click="copyWebhookUrl" class="copy-btn">
                <Copy class="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">HTTP Method</label>
            <select v-model="localNode.config.method" class="form-select" @change="updateNode">
              <option value="POST">POST</option>
              <option value="GET">GET</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
            </select>
          </div>
        </div>

        <!-- Condition Node -->
        <div v-else-if="isCondition" class="config-fields">
          <div class="form-group">
            <label class="form-label">Condition Type</label>
            <select v-model="localNode.config.condition_type" class="form-select" @change="updateNode">
              <option value="simple">Simple Condition</option>
              <option value="advanced">Advanced Expression</option>
            </select>
          </div>
          
          <div v-if="localNode.config.condition_type === 'simple'" class="condition-simple">
            <div class="form-group">
              <label class="form-label">Field</label>
              <input
                v-model="localNode.config.field"
                class="form-input"
                placeholder="data.field"
                @input="updateNode"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">Operator</label>
              <select v-model="localNode.config.operator" class="form-select" @change="updateNode">
                <option value="equals">Equals</option>
                <option value="not_equals">Not Equals</option>
                <option value="contains">Contains</option>
                <option value="not_contains">Not Contains</option>
                <option value="greater_than">Greater Than</option>
                <option value="less_than">Less Than</option>
                <option value="is_empty">Is Empty</option>
                <option value="is_not_empty">Is Not Empty</option>
              </select>
            </div>
            
            <div class="form-group">
              <label class="form-label">Value</label>
              <input
                v-model="localNode.config.value"
                class="form-input"
                placeholder="Expected value"
                @input="updateNode"
              />
            </div>
          </div>
          
          <div v-else class="condition-advanced">
            <div class="form-group">
              <label class="form-label">Expression</label>
              <textarea
                v-model="localNode.config.expression"
                class="form-textarea"
                placeholder="data.field === 'value'"
                rows="3"
                @input="updateNode"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- HTTP Request Action -->
        <div v-else-if="isHttpRequest" class="config-fields">
          <div class="form-group">
            <label class="form-label">URL</label>
            <input
              v-model="localNode.config.url"
              class="form-input"
              placeholder="https://api.example.com/endpoint"
              @input="updateNode"
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">Method</label>
            <select v-model="localNode.config.method" class="form-select" @change="updateNode">
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
              <option value="PATCH">PATCH</option>
            </select>
          </div>
          
          <div class="form-group">
            <label class="form-label">Headers (JSON)</label>
            <textarea
              v-model="headersJson"
              class="form-textarea"
              placeholder='{"Content-Type": "application/json"}'
              rows="3"
              @input="updateHeaders"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label class="form-label">Body (JSON)</label>
            <textarea
              v-model="bodyJson"
              class="form-textarea"
              placeholder='{"key": "value"}'
              rows="4"
              @input="updateBody"
            ></textarea>
          </div>
        </div>

        <!-- Generic Configuration -->
        <div v-else class="config-fields">
          <div class="form-group">
            <label class="form-label">Custom Configuration</label>
            <textarea
              v-model="configJson"
              class="form-textarea"
              placeholder='{"key": "value"}'
              rows="6"
              @input="updateConfig"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Advanced Settings -->
      <div class="config-section">
        <h4 class="section-title">Advanced Settings</h4>
        
        <div class="form-group">
          <label class="form-label">Retry Count</label>
          <input
            v-model.number="localNode.config.retry_count"
            type="number"
            min="0"
            max="10"
            class="form-input"
            @input="updateNode"
          />
        </div>
        
        <div class="form-group">
          <label class="form-label">Timeout (seconds)</label>
          <input
            v-model.number="localNode.config.timeout"
            type="number"
            min="1"
            max="300"
            class="form-input"
            @input="updateNode"
          />
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <input
              v-model="localNode.config.enabled"
              type="checkbox"
              class="form-checkbox"
              @change="updateNode"
            />
            Enabled
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useToast } from 'vue-toastification'
import { X, Copy } from 'lucide-vue-next'

const props = defineProps({
  node: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update-node', 'close'])

const toast = useToast()

// Local state
const localNode = ref({ ...props.node })
const configJson = ref('')
const headersJson = ref('')
const bodyJson = ref('')

// Base URL for webhooks
const baseUrl = computed(() => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
})

// Computed properties for node types
const isGmailTrigger = computed(() => 
  localNode.value.type === 'trigger' && localNode.value.name?.toLowerCase().includes('gmail')
)

const isGmailAction = computed(() => 
  localNode.value.type === 'action' && localNode.value.name?.toLowerCase().includes('gmail')
)

const isSlackAction = computed(() => 
  localNode.value.type === 'action' && localNode.value.name?.toLowerCase().includes('slack')
)

const isWebhookTrigger = computed(() => 
  localNode.value.type === 'webhook' || localNode.value.name?.toLowerCase().includes('webhook')
)

const isCondition = computed(() => 
  localNode.value.type === 'condition'
)

const isHttpRequest = computed(() => 
  localNode.value.type === 'action' && localNode.value.name?.toLowerCase().includes('http')
)

// Initialize configuration
const initializeConfig = () => {
  if (localNode.value.config) {
    configJson.value = JSON.stringify(localNode.value.config, null, 2)
    
    if (localNode.value.config.headers) {
      headersJson.value = JSON.stringify(localNode.value.config.headers, null, 2)
    }
    
    if (localNode.value.config.body) {
      bodyJson.value = JSON.stringify(localNode.value.config.body, null, 2)
    }
  }
}

// Update node configuration
const updateNode = () => {
  emit('update-node', localNode.value.id, {
    name: localNode.value.name,
    config: localNode.value.config
  })
}

// Update headers from JSON
const updateHeaders = () => {
  try {
    localNode.value.config.headers = JSON.parse(headersJson.value)
    updateNode()
  } catch (error) {
    // Invalid JSON, don't update
  }
}

// Update body from JSON
const updateBody = () => {
  try {
    localNode.value.config.body = JSON.parse(bodyJson.value)
    updateNode()
  } catch (error) {
    // Invalid JSON, don't update
  }
}

// Update config from JSON
const updateConfig = () => {
  try {
    localNode.value.config = JSON.parse(configJson.value)
    updateNode()
  } catch (error) {
    // Invalid JSON, don't update
  }
}

// Copy webhook URL
const copyWebhookUrl = async () => {
  try {
    await navigator.clipboard.writeText(`${baseUrl.value}/webhooks/${localNode.value.id}`)
    toast.success('Webhook URL copied to clipboard')
  } catch (error) {
    toast.error('Failed to copy webhook URL')
  }
}

// Watch for prop changes
watch(() => props.node, (newNode) => {
  localNode.value = { ...newNode }
  initializeConfig()
}, { deep: true })

// Initialize on mount
initializeConfig()
</script>

<style scoped>
.node-config-panel {
  @apply w-80 bg-white border-l border-gray-200 flex flex-col h-full;
}

.panel-header {
  @apply flex items-center justify-between p-4 border-b border-gray-200;
}

.panel-title {
  @apply text-lg font-semibold text-gray-900;
}

.close-btn {
  @apply p-1 text-gray-400 hover:text-gray-600 transition-colors;
}

.panel-content {
  @apply flex-1 overflow-y-auto p-4 space-y-6;
}

.config-section {
  @apply space-y-4;
}

.section-title {
  @apply text-sm font-medium text-gray-700 border-b border-gray-200 pb-2;
}

.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-sm font-medium text-gray-700;
}

.form-input {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent;
}

.form-select {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent;
}

.form-textarea {
  @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none;
}

.form-checkbox {
  @apply mr-2 text-blue-600 focus:ring-blue-500;
}

.type-badge {
  @apply inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800;
}

.input-group {
  @apply flex;
}

.copy-btn {
  @apply px-3 py-2 border border-gray-300 border-l-0 rounded-r-md bg-gray-50 hover:bg-gray-100 transition-colors;
}

.condition-simple,
.condition-advanced {
  @apply space-y-3;
}
</style>
