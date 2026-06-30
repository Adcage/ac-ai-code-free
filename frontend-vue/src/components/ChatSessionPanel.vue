<template>
  <div class="chat-session-panel">
    <div class="session-panel-header">
      <span>会话记录</span>
      <a-button type="link" size="small" :loading="loading" @click="$emit('create')">新建会话</a-button>
    </div>
    <div class="session-list">
      <div
        v-for="(session, index) in sessions"
        :key="session.id || index"
        :class="['session-item', normalizeId(session.id) === currentSessionId ? 'active' : '']"
        @click="$emit('select', session.id)"
      >
        <div class="session-title" v-if="!editingSessionId || normalizeId(session.id) !== editingSessionId">
          {{ session.title || `会话 ${index + 1}` }}
        </div>
        <input
          v-else
          class="session-edit-input"
          :value="editingTitle"
          @input="$emit('update:editingTitle', ($event.target as HTMLInputElement).value)"
          @keydown.enter="$emit('confirmRename', session)"
          @blur="$emit('confirmRename', session)"
          @click.stop
        />
        <div class="session-time">{{ formatSessionTime(session.lastMessageTime) }}</div>
        <div class="session-actions" @click.stop>
          <a-button type="text" size="small" class="session-action-btn" @click="$emit('startRename', session)">
            <template #icon><EditOutlined /></template>
          </a-button>
          <a-button type="text" size="small" class="session-action-btn" @click="$emit('delete', session)">
            <template #icon><DeleteOutlined /></template>
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'

export interface SessionItem {
  id?: string | number
  title?: string
  lastMessageTime?: string
  [key: string]: unknown
}

const props = withDefaults(
  defineProps<{
    sessions: SessionItem[]
    currentSessionId: string
    loading?: boolean
    editingSessionId?: string
    editingTitle?: string
  }>(),
  {
    loading: false,
    editingSessionId: '',
    editingTitle: '',
  },
)

defineEmits<{
  select: [sessionId?: string | number]
  create: []
  startRename: [session: SessionItem]
  confirmRename: [session: SessionItem]
  delete: [session: SessionItem]
  'update:editingTitle': [value: string]
}>()

const normalizeId = (id?: string | number | null) => {
  if (id === undefined || id === null) return ''
  return String(id)
}

const formatSessionTime = (time?: string) => {
  if (!time) return '暂无消息'
  const date = new Date(time)
  if (Number.isNaN(date.getTime())) return '暂无消息'
  return date.toLocaleString()
}
</script>

<style scoped>
.chat-session-panel {
  padding: 14px 16px 12px;
  border-bottom: 1px solid rgba(220, 207, 196, 0.9);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(252, 250, 247, 0.92));
}

.session-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.session-list {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.session-item {
  min-width: 140px;
  max-width: 180px;
  border: 1px solid rgba(220, 207, 196, 0.92);
  border-radius: 14px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all var(--transition-normal);
  background: rgba(255, 255, 255, 0.92);
  position: relative;
  flex-shrink: 0;
  box-shadow: 0 8px 18px rgba(28, 24, 21, 0.04);
}

.session-item:hover {
  border-color: rgba(200, 90, 62, 0.34);
  transform: translateY(-1px);
}

.session-item.active {
  border-color: rgba(200, 90, 62, 0.34);
  background: var(--color-primary-bg);
  box-shadow: 0 12px 24px rgba(28, 24, 21, 0.06);
}

.session-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-edit-input {
  width: 100%;
  font-size: 12px;
  border: 1px solid var(--color-cta);
  border-radius: 8px;
  padding: 2px 6px;
  outline: none;
  background: var(--color-background);
  color: var(--color-text);
}

.session-time {
  font-size: 11px;
  color: var(--color-text-tertiary);
  margin-top: 4px;
}

.session-actions {
  position: absolute;
  top: 4px;
  right: 4px;
  display: none;
  gap: 2px;
}

.session-item:hover .session-actions {
  display: flex;
}

.session-action-btn {
  width: 20px;
  height: 20px;
  padding: 0;
  font-size: 11px;
  color: var(--color-text-tertiary);
}
</style>
