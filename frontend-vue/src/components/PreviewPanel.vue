<template>
  <div class="preview-panel">
    <div class="preview-header">
      <a-radio-group v-model:value="previewType" size="small" button-style="solid">
        <a-radio-button value="desktop">桌面端</a-radio-button>
        <a-radio-button value="mobile">移动端</a-radio-button>
      </a-radio-group>
      <a-space>
        <a-button size="small" @click="showVersionPanel = !showVersionPanel" v-if="appId">
          <template #icon><HistoryOutlined /></template>
          版本
        </a-button>
        <a-button size="small" :type="editMode ? 'primary' : 'default'" @click="toggleEditMode">
          {{ editMode ? '退出编辑模式' : '进入编辑模式' }}
        </a-button>
        <a-button size="small" :disabled="!selectedElement" @click="$emit('clearSelectedElement')">清除选中</a-button>
        <a-button size="small" @click="refreshIframe">
          <template #icon><ReloadOutlined /></template>
        </a-button>
      </a-space>
    </div>
    <a-alert v-if="previewWarning" class="preview-warning" type="warning" show-icon :message="previewWarning" />
    <div :class="['preview-body', previewType]">
      <iframe
        v-if="iframeUrl"
        :src="iframeUrl"
        frameborder="0"
        class="preview-iframe"
        ref="iframeRef"
        @load="handleIframeLoad"
      ></iframe>
      <div v-else class="preview-empty">
        <div class="empty-content">
          <div class="empty-icon">预览</div>
          <p>{{ previewEmptyText }}</p>
        </div>
      </div>
    </div>

    <div v-if="showVersionPanel" class="version-panel">
      <div class="version-panel-header">
        <span>版本历史</span>
        <a-button type="text" size="small" @click="showVersionPanel = false">
          <template #icon><CloseCircleOutlined /></template>
        </a-button>
      </div>
      <div class="version-panel-body">
        <div v-if="versionLoading" class="version-loading"><LoadingOutlined /> 加载中...</div>
        <div v-else-if="versionList.length === 0" class="version-empty">暂无版本记录</div>
        <div v-else class="version-list">
          <div v-for="v in versionList" :key="v.id" class="version-item">
            <div class="version-no">v{{ v.versionNo }}</div>
            <div class="version-info">
              <span :class="['version-status', v.status]">{{ v.status === 'created' ? '已创建' : v.status }}</span>
              <span class="version-time">{{ formatVersionTime(v.createTime) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  HistoryOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons-vue'
import { listAppVersions } from '@/api/appVersionController'
import { createVisualEditor, type ElementInfo } from '@/utils/visualEditor'

export interface PreviewStatusType {
  status: 'idle' | 'generating' | 'checking' | 'ready' | 'failed'
  warning: string
}

const props = withDefaults(
  defineProps<{
    iframeUrl: string
    previewStatus: 'idle' | 'generating' | 'checking' | 'ready' | 'failed'
    previewWarning?: string
    appId?: string
    selectedElement?: ElementInfo | null
  }>(),
  {
    previewWarning: '',
    appId: '',
    selectedElement: null,
  },
)

const emit = defineEmits<{
  iframeLoad: [iframe: HTMLIFrameElement | null]
  elementSelected: [element: ElementInfo]
  modeChange: [enabled: boolean]
  clearSelectedElement: []
}>()

const previewType = ref('desktop')
const showVersionPanel = ref(false)
const versionLoading = ref(false)
const versionList = ref<API.AppVersionVO[]>([])
const editMode = ref(false)
const iframeRef = ref<HTMLIFrameElement>()

const previewEmptyText = computed(() => {
  if (props.previewStatus === 'generating') return '应用正在生成中，完成后将在此展示效果'
  if (props.previewStatus === 'checking') return '正在检查预览资源...'
  if (props.previewStatus === 'failed') {
    return props.previewWarning || '本次生成未产出可预览页面，请根据左侧错误信息调整后重试'
  }
  return '暂无可预览内容，生成完成后将在此展示效果'
})

// 可视化编辑器
const visualEditor = createVisualEditor({
  getIframe: () => iframeRef.value,
  onElementHover: () => {},
  onElementSelected: (element) => {
    emit('elementSelected', element)
  },
  onModeChange: (enabled) => {
    editMode.value = enabled
    emit('modeChange', enabled)
    if (!enabled) {
      emit('clearSelectedElement')
    }
  },
})

const handleIframeLoad = () => {
  if (!iframeRef.value) return
  try {
    const text = iframeRef.value.contentDocument?.body?.innerText || ''
    if (text.includes('Whitelabel Error Page') || text.includes('No static resource')) {
      // 通知父组件 iframe 加载了错误页面
      return
    }
  } catch {
    // 跨域访问限制，忽略
  }
  visualEditor.handleIframeLoad()
  emit('iframeLoad', iframeRef.value)
}

const toggleEditMode = () => {
  if (!props.iframeUrl) {
    message.warning('暂无可编辑预览，请先生成页面内容')
    return
  }
  if (editMode.value) {
    visualEditor.exitEditMode()
    return
  }
  const entered = visualEditor.enterEditMode()
  if (!entered) {
    message.warning('编辑模式初始化失败，请刷新预览后重试')
  }
}

const refreshIframe = () => {
  if (props.iframeUrl) {
    visualEditor.clearSelection()
    emit('clearSelectedElement')
  }
}

const formatVersionTime = (time?: string) => {
  if (!time) return ''
  const date = new Date(time)
  if (Number.isNaN(date.getTime())) return ''
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}小时前`
  return date.toLocaleDateString()
}

const loadVersions = async () => {
  if (!props.appId) return
  versionLoading.value = true
  try {
    const res = await listAppVersions({ appId: Number(props.appId) })
    if (res.data?.code === 0) {
      versionList.value = res.data?.data || []
    }
  } finally {
    versionLoading.value = false
  }
}

watch(showVersionPanel, (val) => {
  if (val) loadVersions()
})

defineExpose({ visualEditor, iframeRef })
</script>

<style scoped>
.preview-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  min-width: 0;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border);
}

.preview-warning {
  margin: 8px 16px 0;
}

.preview-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 16px;
  background: var(--color-background);
}

.preview-body.desktop {
  align-items: stretch;
}

.preview-body.mobile {
  padding: 16px;
}

.preview-body.mobile .preview-iframe {
  width: 375px;
  max-height: 812px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: #fff;
}

.preview-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  width: 100%;
}

.empty-content {
  text-align: center;
  color: var(--color-text-tertiary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.3;
}

.version-panel {
  border-top: 1px solid var(--color-border);
  max-height: 300px;
  overflow-y: auto;
}

.version-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
  font-weight: 500;
}

.version-panel-body {
  padding: 8px 16px;
}

.version-loading,
.version-empty {
  text-align: center;
  padding: 16px;
  color: var(--color-text-tertiary);
  font-size: 13px;
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.version-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
}

.version-no {
  font-weight: 600;
  color: var(--color-primary);
  font-size: 13px;
}

.version-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.version-status {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
}

.version-status.created {
  background: #f6ffed;
  color: #52c41a;
}

.version-time {
  color: var(--color-text-tertiary);
}
</style>
