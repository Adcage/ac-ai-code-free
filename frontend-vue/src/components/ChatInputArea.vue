<template>
  <div class="chat-input-area">
    <div class="input-row">
      <a-textarea
        v-model:value="inputText"
        :placeholder="placeholder"
        :auto-size="{ minRows: 1, maxRows: 4 }"
        :disabled="disabled || generating"
        @press-enter="handleEnter"
        class="chat-textarea"
      />
      <div class="input-actions">
        <a-tooltip title="优化提示词">
          <a-button
            type="text"
            size="small"
            :disabled="!inputText.trim() || generating"
            :loading="enhancing"
            @click="$emit('enhance', inputText)"
          >
            <template #icon><BulbOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-button
          type="primary"
          size="small"
          :disabled="!inputText.trim() || generating"
          @click="handleSend"
        >
          <template #icon><SendOutlined /></template>
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { BulbOutlined, SendOutlined } from '@ant-design/icons-vue'

const props = withDefaults(
  defineProps<{
    generating?: boolean
    enhancing?: boolean
    placeholder?: string
    disabled?: boolean
  }>(),
  {
    generating: false,
    enhancing: false,
    placeholder: '输入你的需求，按 Enter 发送...',
    disabled: false,
  },
)

const emit = defineEmits<{
  send: [message: string]
  enhance: [message: string]
}>()

const inputText = ref('')

const handleSend = () => {
  const msg = inputText.value.trim()
  if (!msg || props.generating) return
  emit('send', msg)
  inputText.value = ''
}

const handleEnter = (e: KeyboardEvent) => {
  if (e.shiftKey) return // Shift+Enter 换行
  e.preventDefault()
  handleSend()
}

defineExpose({ inputText })
</script>

<style scoped>
.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid var(--color-border);
  background: var(--color-background);
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.chat-textarea {
  flex: 1;
  border-radius: 8px;
  resize: none;
}

.input-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
</style>
