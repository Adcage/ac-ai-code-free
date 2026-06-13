<template>
  <div id="appGeneratorPage">
    <div class="top-nav">
      <div class="left">
        <a-button type="text" @click="handleBack">
          <template #icon><left-outlined /></template>
        </a-button>
        <span class="app-name">{{ app?.appName || '新应用' }}</span>
      </div>
      <div class="right">
        <a-space>
          <span class="status-tag" v-if="app?.deployKey">
            <a-badge status="success" text="已部署" />
          </span>
          <a-tag v-if="app?.coverTaskStatus" :color="coverTaskStatusColor(app.coverTaskStatus)">
            {{ formatCoverTaskStatus(app.coverTaskStatus, app.coverRetryCount) }}
          </a-tag>
          <a-tag v-if="app?.codeGenType" color="blue">{{ formatCodeGenType(app.codeGenType) }}</a-tag>
          <a-button :loading="downloadLoading" :disabled="!canDownload" @click="doDownload" class="download-btn">
            <template #icon><download-outlined /></template>
            下载代码
          </a-button>
          <a-button type="primary" :loading="deployLoading" @click="doDeploy" class="deploy-btn">
            <template #icon><cloud-upload-outlined /></template>
            部署
          </a-button>
        </a-space>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧对话区 -->
      <div class="chat-panel" :style="{ width: `${chatPanelWidth}px` }">
        <div class="session-panel">
          <div class="session-panel-header">
            <span>会话记录</span>
            <a-button type="link" size="small" :loading="sessionLoading" @click="handleCreateSession"
              >新建会话</a-button
            >
          </div>
          <div class="session-list">
            <div
              v-for="(session, index) in sessions"
              :key="session.id || index"
              :class="['session-item', normalizeId(session.id) === currentSessionId ? 'active' : '']"
              @click="handleSwitchSession(session.id)"
            >
              <div class="session-title" v-if="!editingSessionId || normalizeId(session.id) !== editingSessionId">
                {{ session.title || `会话 ${index + 1}` }}
              </div>
              <input
                v-else
                class="session-edit-input"
                v-model="editingTitle"
                @keydown.enter="confirmRename(session)"
                @blur="confirmRename(session)"
                @click.stop
              />
              <div class="session-time">{{ formatSessionTime(session.lastMessageTime) }}</div>
              <div class="session-actions" @click.stop>
                <a-button type="text" size="small" class="session-action-btn" @click="startRename(session)">
                  <template #icon><EditOutlined /></template>
                </a-button>
                <a-button type="text" size="small" class="session-action-btn" @click="confirmDeleteSession(session)">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </div>
            </div>
          </div>
        </div>
        <div class="message-list" ref="messageListRef">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message-item', msg.role === 'user' ? 'user-msg' : 'ai-msg']"
          >
            <a-avatar :src="msg.role === 'user' ? loginUserStore.loginUser.userAvatar : '/ai-avatar.png'" />
            <div class="message-body">
              <div class="message-content">
                <template v-if="msg.role === 'ai'">
                  <template
                    v-for="parsed in [parseAiMessage(msg.content, msg.toolEvents || [])]"
                    :key="`parsed-${index}`"
                  >
                    <div v-if="parsed.aiText" class="message-text" v-html="renderMarkdown(parsed.aiText)"></div>
                    <details v-if="parsed.toolEvents.length" class="tool-call-card">
                      <summary class="tool-call-summary">
                        <span class="tool-call-title">工具调用（{{ parsed.toolEvents.length }}）</span>
                        <span class="tool-call-hint">点击查看执行详情</span>
                      </summary>
                      <div class="tool-call-list">
                        <div
                          v-for="(eventItem, toolIndex) in parsed.toolEvents"
                          :key="`tool-${index}-${toolIndex}`"
                          class="tool-call-item"
                        >
                          <span :class="['tool-call-tag', eventItem.type]">
                            {{ eventItem.type === 'request' ? '调用中' : '已完成' }}
                          </span>
                          <span class="tool-call-text">{{ eventItem.text }}</span>
                        </div>
                      </div>
                    </details>
                    <div v-if="msg.workflowSteps?.length" class="workflow-steps message-workflow-steps">
                      <div class="workflow-steps-title">工作流进度</div>
                      <div class="workflow-steps-list">
                        <div
                          v-for="step in msg.workflowSteps"
                          :key="step.step"
                          :class="['workflow-step-item', step.status]"
                        >
                          <div class="workflow-step-icon">
                            <check-circle-outlined v-if="step.status === 'completed'" />
                            <loading-outlined v-else-if="step.status === 'running'" />
                            <close-circle-outlined v-else-if="step.status === 'error'" />
                            <clock-circle-outlined v-else />
                          </div>
                          <div class="workflow-step-content">
                            <div class="workflow-step-name">{{ step.message }}</div>
                            <div v-if="step.status === 'error'" class="workflow-step-error">
                              {{ step.errorMessage || step.message }}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>
                </template>
                <div v-else class="message-text" v-html="renderMarkdown(msg.content)"></div>
              </div>
            </div>
          </div>
          <div v-if="generating" class="generating-indicator"><loading-outlined /> AI 正在思考并生成代码...</div>
        </div>

        <div v-if="streamWarning" class="stream-warning">
          <a-alert type="warning" show-icon :message="streamWarning" />
          <a-button type="link" size="small" @click="handleReloadCurrentSession">重新加载当前会话</a-button>
        </div>

        <div v-if="selectedElement" class="selected-element-panel">
          <a-alert type="info" show-icon>
            <template #message>当前选中元素</template>
            <template #description>
              <div class="selected-element-content">
                <div>标签：{{ selectedElement.tagName }}</div>
                <div>页面路径：{{ selectedElement.pagePath || '/' }}</div>
                <div>选择器：{{ selectedElement.selector || '未生成' }}</div>
                <div>文本：{{ selectedElement.textContent || '（无可见文本）' }}</div>
              </div>
            </template>
            <template #action>
              <a-button size="small" type="link" @click="clearSelectedElement">清除</a-button>
            </template>
          </a-alert>
        </div>

        <div class="input-area">
          <div class="input-wrapper">
            <a-textarea
              v-model:value="inputText"
              :placeholder="inputPlaceholder"
              :auto-size="{ minRows: 2, maxRows: 6 }"
              @pressEnter="handleEnter"
            />
            <div class="input-footer">
              <a-space>
                <a-button type="text" size="small" disabled>
                  <template #icon><paper-clip-outlined /></template>上传
                </a-button>
                <a-button
                  type="text"
                  size="small"
                  :disabled="!inputText.trim()"
                  :loading="enhancingInput"
                  @click="doEnhanceInput"
                >
                  <template #icon><thunderbolt-outlined /></template>优化
                </a-button>
              </a-space>
              <a-button type="primary" shape="circle" size="small" :disabled="generating || !inputText" @click="doChat">
                <template #icon><arrow-up-outlined /></template>
              </a-button>
            </div>
          </div>
        </div>
      </div>

      <div class="panel-splitter" @mousedown="startResize" />

      <!-- 右侧预览区 -->
      <div class="preview-panel">
        <div class="preview-header">
          <a-radio-group v-model:value="previewType" size="small" button-style="solid">
            <a-radio-button value="desktop">桌面端</a-radio-button>
            <a-radio-button value="mobile">移动端</a-radio-button>
          </a-radio-group>
          <a-space>
            <a-button size="small" @click="showVersionPanel = !showVersionPanel">
              <template #icon><HistoryOutlined /></template>
              版本
            </a-button>
            <a-button size="small" :type="editMode ? 'primary' : 'default'" @click="toggleEditMode">
              {{ editMode ? '退出编辑模式' : '进入编辑模式' }}
            </a-button>
            <a-button size="small" :disabled="!selectedElement" @click="clearSelectedElement">清除选中</a-button>
            <a-button size="small" @click="refreshIframe">
              <template #icon><reload-outlined /></template>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  LeftOutlined,
  CloudUploadOutlined,
  DownloadOutlined,
  ReloadOutlined,
  PaperClipOutlined,
  ThunderboltOutlined,
  ArrowUpOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  HistoryOutlined,
} from '@ant-design/icons-vue'
import {
  createChatSession,
  deployApp,
  getAppVoById,
  listChatHistoryByPage,
  listChatSession,
  renameSession,
  deleteSession,
  enhancePrompt,
} from '@/api/appController'
import { listAppVersions } from '@/api/appVersionController'
import { useLoginUserStore } from '@/stores/LoginUser'
import { createVisualEditor, type ElementInfo } from '@/utils/visualEditor'

const route = useRoute()
const router = useRouter()
const loginUserStore = useLoginUserStore()
const appId = String(route.params.id ?? '')

const app = ref<API.AppVO>()
type WorkflowStep = {
  step: string
  status: 'pending' | 'running' | 'completed' | 'error'
  message?: string
  errorMessage?: string
}

type ChatMessage = {
  role: 'user' | 'ai'
  content: string
  status?: string
  toolEvents?: ToolEvent[]
  workflowSteps?: WorkflowStep[]
}

const messages = ref<ChatMessage[]>([])
const sessions = ref<API.ChatSessionVO[]>([])
const currentSessionId = ref<string>()
const inputText = ref('')
const generating = ref(false)
const enhancingInput = ref(false)
const workflowSteps = ref<WorkflowStep[]>([])
const deployLoading = ref(false)
const downloadLoading = ref(false)
const sessionLoading = ref(false)
const sessionInitializing = ref(false)
const previewType = ref('desktop')
const showVersionPanel = ref(false)
const versionLoading = ref(false)
const versionList = ref<API.AppVersionVO[]>([])
const iframeUrl = ref('')
const iframeRef = ref<HTMLIFrameElement>()
const messageListRef = ref<HTMLElement>()
const streamWarning = ref('')
const previewWarning = ref('')
const previewStatus = ref<'idle' | 'generating' | 'checking' | 'ready' | 'failed'>('idle')
const entryPathStorageKey = `app_generate_entry_${appId}`
const chatPanelWidth = ref(450)
const resizing = ref(false)
const resizeStartX = ref(0)
const resizeStartWidth = ref(450)
const selectedElement = ref<ElementInfo | null>(null)
const editMode = ref(false)
const editingSessionId = ref<string>('')
const editingTitle = ref('')

const isOwner = computed(() => {
  const loginUserId = loginUserStore.loginUser?.id
  return !!(loginUserId && app.value?.userId && String(loginUserId) === String(app.value.userId))
})

const canDownload = computed(() => isOwner.value)

const inputPlaceholder = computed(() => {
  if (selectedElement.value) {
    return '已选择页面元素，请描述要修改的内容...'
  }
  return '描述具体的需求，例如：修改配色为深色模式...'
})

const previewEmptyText = computed(() => {
  if (previewStatus.value === 'generating') {
    return '应用正在生成中，完成后将在此展示效果'
  }
  if (previewStatus.value === 'checking') {
    return '正在检查预览资源...'
  }
  if (previewStatus.value === 'failed') {
    return previewWarning.value || '本次生成未产出可预览页面，请根据左侧错误信息调整后重试'
  }
  return '暂无可预览内容，生成完成后将在此展示效果'
})

type ToolEvent = {
  type: 'request' | 'executed'
  text: string
}

const visualEditor = createVisualEditor({
  getIframe: () => iframeRef.value,
  onElementHover: () => {},
  onElementSelected: (element) => {
    selectedElement.value = element
  },
  onModeChange: (enabled) => {
    editMode.value = enabled
    if (!enabled) {
      selectedElement.value = null
    }
  },
})

const normalizeId = (id?: string | number | null) => {
  if (id === undefined || id === null) {
    return ''
  }
  return String(id)
}

const ensureValidAppId = () => {
  if (!appId) {
    message.error('应用 ID 无效，请返回列表重新进入')
    return false
  }
  return true
}

const loadSessions = async () => {
  if (!ensureValidAppId()) {
    return
  }
  sessionLoading.value = true
  try {
    const res = await listChatSession({ appId: appId as any })
    if (res.data?.code === 0) {
      sessions.value = res.data.data || []
      return
    }
    message.error('加载会话失败，' + (res.data?.message || '请稍后重试'))
  } finally {
    sessionLoading.value = false
  }
}

const createSession = async () => {
  if (!ensureValidAppId()) {
    return undefined
  }
  const res = await createChatSession({ appId: appId as any })
  if (res.data?.code === 0 && res.data.data) {
    const sessionId = normalizeId(res.data.data)
    await loadSessions()
    return sessionId
  }
  message.error('创建会话失败，' + (res.data?.message || '请稍后重试'))
  return undefined
}

const loadRemoteHistory = async (sessionId: string) => {
  if (!ensureValidAppId()) {
    return
  }
  const res = await listChatHistoryByPage({
    appId: appId as any,
    sessionId: sessionId as any,
    pageNum: 1,
    pageSize: 200,
  })
  if (res.data?.code === 0) {
    const historyList = res.data.data?.records || []
    messages.value = historyList.map((item) => ({
      role: item.messageType === 'user' ? 'user' : 'ai',
      content: item.message || '',
      status: item.status || '',
      toolEvents: normalizeToolEvents(item.toolEvents || []),
    }))
    scrollToBottom()
  }
}

const normalizeToolEvents = (events?: API.ToolEventVO[]) => {
  if (!events || events.length === 0) {
    return []
  }
  return events
    .filter((item) => (item.type === 'request' || item.type === 'executed') && !!item.text)
    .map((item) => ({
      type: item.type as 'request' | 'executed',
      text: item.text as string,
    }))
}

/**
 * 加载应用信息
 */
const loadApp = async () => {
  if (!ensureValidAppId()) {
    return
  }
  const res = await getAppVoById({ id: appId as any })
  if (res.data?.code === 0) {
    app.value = res.data.data

    await loadSessions()
    if (sessions.value.length > 0 && sessions.value[0].id) {
      currentSessionId.value = normalizeId(sessions.value[0].id)
      await loadRemoteHistory(currentSessionId.value)
      await updatePreview()
    } else {
      const newSessionId = await createSession()
      if (newSessionId) {
        currentSessionId.value = newSessionId
      }
      if (app.value?.initPrompt && currentSessionId.value) {
        messages.value.push({ role: 'user', content: app.value.initPrompt, status: 'success', toolEvents: [] })
        startSSE(app.value.initPrompt, currentSessionId.value)
      }
    }
    return
  }
  message.error('加载应用失败，' + (res.data?.message || '请稍后重试'))
}

/**
 * SSE 对话逻辑
 */
const startSSE = (userMsg: string, sessionId: string) => {
  generating.value = true
  streamWarning.value = ''
  iframeUrl.value = ''
  previewWarning.value = ''
  previewStatus.value = 'generating'
  workflowSteps.value = [
    { step: 'image_collect', status: 'pending', message: '收集素材' },
    { step: 'prompt_enhancer', status: 'pending', message: '增强 prompt' },
    { step: 'router', status: 'pending', message: '判断类型' },
    { step: 'code_generator', status: 'pending', message: '生成代码' },
    { step: 'code_quality_check', status: 'pending', message: '质量检查' },
    { step: 'project_builder', status: 'pending', message: '构建' },
  ]
  let streamCompleted = false
  const aiMsgIndex = messages.value.length
  messages.value.push({ role: 'ai', content: '', status: 'running', workflowSteps: workflowSteps.value })
  const isStructuredToolMode =
    app.value?.codeGenType === 'vue_project' ||
    app.value?.codeGenType === 'multi-file' ||
    app.value?.codeGenType === 'single_file'

  const baseUrl = import.meta.env.VITE_API_BASE_URL
  const eventSource = new EventSource(
    `${baseUrl}/app/chat/gen/code/stream?appId=${appId}&sessionId=${sessionId}&message=${encodeURIComponent(userMsg)}`,
    { withCredentials: true },
  )

  eventSource.addEventListener('meta', (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)
      if (data.sessionId) {
        currentSessionId.value = normalizeId(data.sessionId)
      }
    } catch (e) {
      console.error('SSE Meta Parse Error', e)
    }
  })

  const stopGenerating = (delayPreviewRefresh = false) => {
    eventSource.close()
    if (streamCompleted) {
      streamWarning.value = ''
    }
    if (generating.value) {
      generating.value = false
      loadSessions()
      if (delayPreviewRefresh) {
        setTimeout(() => {
          messages.value[aiMsgIndex].status = streamCompleted ? 'success' : 'failed'
          updatePreview()
        }, 500)
      } else {
        messages.value[aiMsgIndex].status = streamCompleted ? 'success' : 'failed'
        updatePreview()
      }
    }
  }

  eventSource.addEventListener('business-error', (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)
      const errorMsg = data.message || '操作失败'
      messages.value[aiMsgIndex].content += `\n\n[错误] ${errorMsg}`
      messages.value[aiMsgIndex].status = 'failed'
      previewStatus.value = 'failed'
      previewWarning.value = errorMsg
      message.error(errorMsg)
    } catch {
      message.error('操作失败')
    }
    stopGenerating()
  })

  eventSource.addEventListener('done', () => {
    streamCompleted = true
    stopGenerating(true)
  })

  eventSource.onmessage = (event) => {
    const rawData = event.data
    if (rawData === '[DONE]') {
      streamCompleted = true
      stopGenerating(true)
      return
    }

    try {
      const data = JSON.parse(rawData)
      if (data.d === '[DONE]') {
        streamCompleted = true
        stopGenerating(true)
        return
      }
      const chunk = data.d || ''
      appendStreamChunk(aiMsgIndex, chunk, isStructuredToolMode)
      scrollToBottom()
    } catch {
      if (rawData.includes('[DONE]')) {
        streamCompleted = true
        stopGenerating(true)
      }
    }
  }

  eventSource.onerror = (err) => {
    console.error('SSE Error', err)
    if (!streamCompleted) {
      streamWarning.value = '连接中断，本次 AI 输出可能未完整保存。可重新加载当前会话查看已落库内容。'
      messages.value[aiMsgIndex].status = 'failed'
      previewStatus.value = 'failed'
      previewWarning.value = '连接中断，本次 AI 输出可能未完整保存。'
      message.warning('连接中断，已停止本次生成')
    }
    stopGenerating()
  }
}

const handleReloadCurrentSession = async () => {
  if (!currentSessionId.value) {
    return
  }
  await loadRemoteHistory(currentSessionId.value)
  streamWarning.value = ''
}

const buildSelectedElementPrompt = (userInput: string) => {
  if (!selectedElement.value) {
    return userInput
  }
  const target = selectedElement.value
  const text = target.textContent || '（无可见文本）'
  const selector = target.selector || '（无可用选择器）'
  const pagePath = target.pagePath || '/'
  return [
    '选中元素信息：',
    `- 页面路径：${pagePath}`,
    `- 标签：${target.tagName}`,
    `- 选择器：${selector}`,
    `- 当前内容：${text}`,
    '',
    `修改需求：${userInput}`,
  ].join('\n')
}

const appendStreamChunk = (aiMsgIndex: number, chunk: string, structuredToolMode: boolean) => {
  if (!structuredToolMode) {
    messages.value[aiMsgIndex].content += chunk
    return
  }
  try {
    const messageObj = JSON.parse(chunk)
    const type = messageObj.type
    if (type === 'ai_response') {
      messages.value[aiMsgIndex].content += messageObj.data || ''
      return
    }
    if (type === 'tool_request') {
      const text = formatToolText(messageObj.name, messageObj.arguments, 'request')
      appendToolEvent(aiMsgIndex, { type: 'request', text })
      return
    }
    if (type === 'tool_executed') {
      const executedText = formatToolText(messageObj.name, messageObj.arguments, 'executed', messageObj.result)
      appendToolEvent(aiMsgIndex, { type: 'executed', text: executedText })
      return
    }
    if (type === 'workflow_event') {
      handleWorkflowEvent(messageObj, aiMsgIndex)
      return
    }
    messages.value[aiMsgIndex].content += chunk
  } catch {
    messages.value[aiMsgIndex].content += chunk
  }
}

const appendToolEvent = (aiMsgIndex: number, eventItem: ToolEvent) => {
  const targetMessage = messages.value[aiMsgIndex]
  if (!targetMessage) {
    return
  }
  if (!targetMessage.toolEvents) {
    targetMessage.toolEvents = []
  }
  targetMessage.toolEvents.push(eventItem)
}

const handleWorkflowEvent = (eventData: any, aiMsgIndex: number) => {
  const eventType = eventData.event
  const data = eventData.data || {}

  if (eventType === 'workflow_start') {
    workflowSteps.value.forEach((step, index) => {
      step.status = index === 0 ? 'running' : 'pending'
    })
    return
  }

  if (eventType === 'step_started') {
    const stepName = data.step
    workflowSteps.value.forEach((step) => {
      if (step.step === stepName) {
        step.status = 'running'
      } else if (step.status === 'running') {
        step.status = 'pending'
      }
    })
    return
  }

  if (eventType === 'step_completed') {
    const stepName = data.step
    const stepIndex = workflowSteps.value.findIndex((s) => s.step === stepName)
    if (stepIndex >= 0) {
      workflowSteps.value[stepIndex].status = 'completed'
      if (stepIndex + 1 < workflowSteps.value.length) {
        workflowSteps.value[stepIndex + 1].status = 'running'
      }
    }
    return
  }

  if (eventType === 'workflow_completed') {
    workflowSteps.value.forEach((step) => {
      if (step.status !== 'completed') {
        step.status = 'completed'
      }
    })
    if (data.codeGenType && app.value) {
      app.value.codeGenType = data.codeGenType
    }
    if (!messages.value[aiMsgIndex].content.trim()) {
      const codeGenTypeText = data.codeGenType ? formatCodeGenType(data.codeGenType) : '代码'
      messages.value[aiMsgIndex].content = `代码生成完成：已生成 ${codeGenTypeText} 产物`
    }
    return
  }

  if (eventType === 'workflow_error') {
    workflowSteps.value.forEach((step) => {
      if (step.status === 'running') {
        step.status = 'error'
        step.errorMessage = data.message || '执行失败'
      }
    })
    return
  }
}

const parsePathFromArguments = (argumentsText?: string) => {
  if (!argumentsText) {
    return ''
  }
  try {
    const argsObj = JSON.parse(argumentsText)
    return argsObj.relativeFilePath || argsObj.relativeDirPath || ''
  } catch {
    return ''
  }
}

const formatToolText = (
  toolName?: string,
  argumentsText?: string,
  stage: 'request' | 'executed' = 'request',
  result?: string,
) => {
  const path = parsePathFromArguments(argumentsText)
  const requestMap: Record<string, string> = {
    writeFile: path ? `准备写入文件 ${path}` : '准备写入文件',
    readFile: path ? `准备读取文件 ${path}` : '准备读取文件',
    modifyFile: path ? `准备修改文件 ${path}` : '准备修改文件',
    deleteFile: path ? `准备删除文件 ${path}` : '准备删除文件',
    readDir: path ? `准备读取目录 ${path}` : '准备读取目录结构',
  }
  const executedMap: Record<string, string> = {
    writeFile: path ? `已写入文件 ${path}` : '文件写入成功',
    readFile: path ? `已读取文件 ${path}` : '文件读取成功',
    modifyFile: path ? `已修改文件 ${path}` : '文件修改成功',
    deleteFile: path ? `已删除文件 ${path}` : '文件删除成功',
    readDir: path ? `目录结构读取完成 ${path}` : '目录结构读取完成',
  }
  if (stage === 'request') {
    return requestMap[toolName || ''] || `正在执行工具 ${toolName || ''}`.trim()
  }
  if (result && String(result).startsWith('文件修改失败')) {
    return result
  }
  if (result && String(result).startsWith('禁止删除关键文件')) {
    return result
  }
  return executedMap[toolName || ''] || result || `工具执行成功 ${toolName || ''}`.trim()
}

const ensureSessionReady = async () => {
  if (currentSessionId.value) {
    return currentSessionId.value
  }
  if (sessionInitializing.value) {
    return undefined
  }
  sessionInitializing.value = true
  try {
    const sessionId = await createSession()
    if (sessionId) {
      currentSessionId.value = sessionId
    }
    return sessionId
  } finally {
    sessionInitializing.value = false
  }
}

const doChat = async () => {
  const rawMessage = inputText.value.trim()
  if (generating.value || !rawMessage) return
  const sessionId = await ensureSessionReady()
  if (!sessionId) {
    message.warning('会话初始化中，请稍后再试')
    return
  }
  const promptMessage = buildSelectedElementPrompt(rawMessage)
  messages.value.push({ role: 'user', content: rawMessage, status: 'success', toolEvents: [] })
  inputText.value = ''
  startSSE(promptMessage, sessionId)
}

const doEnhanceInput = async () => {
  const prompt = inputText.value.trim()
  if (!prompt) return
  enhancingInput.value = true
  try {
    const res = await enhancePrompt({ prompt })
    if (res.data?.code === 0) {
      const enhanced = res.data?.data
      if (enhanced && enhanced.trim()) {
        inputText.value = enhanced
        message.success('提示词优化完成')
      } else {
        message.warning('AI 未返回有效的优化结果，请重试或直接发送')
      }
    } else {
      message.error('优化失败，' + (res.data?.message ?? '未知错误'))
    }
  } catch (e: unknown) {
    message.error('优化失败，' + (e instanceof Error ? e.message : String(e)))
  } finally {
    enhancingInput.value = false
  }
}

const handleEnter = (e: KeyboardEvent) => {
  if (!e.shiftKey) {
    e.preventDefault()
    doChat()
  }
}

/**
 * 更新预览
 */
const updatePreview = async () => {
  const codeGenType = app.value?.codeGenType || 'single_file'
  const deployUrlPrefix = import.meta.env.VITE_APP_DEPLOY_URL_PREFIX
  previewWarning.value = ''
  selectedElement.value = null
  if (!hasPreviewCandidate()) {
    iframeUrl.value = ''
    previewStatus.value = hasLatestGenerationFailure() ? 'failed' : 'idle'
    if (previewStatus.value === 'failed') {
      previewWarning.value = extractLatestFailureReason() || '本次生成未产出可预览页面，请根据左侧错误信息调整后重试'
    }
    return
  }
  previewStatus.value = 'checking'
  const nextUrl = buildPreviewUrl(codeGenType, deployUrlPrefix)
  const resourceAvailable = await checkPreviewResource(nextUrl)
  if (!resourceAvailable) {
    iframeUrl.value = ''
    previewStatus.value = 'failed'
    const latestFailureReason = extractLatestFailureReason()
    previewWarning.value = latestFailureReason
      ? `预览资源不存在，通常是中间生成或构建失败导致目标文件未生成。最近一次失败原因：${latestFailureReason}`
      : '预览资源不存在，通常是中间生成或构建失败导致目标文件未生成。'
    return
  }
  previewStatus.value = 'ready'
  iframeUrl.value = nextUrl
}

const buildPreviewUrl = (codeGenType: string, deployUrlPrefix: string) => {
  if (codeGenType === 'vue_project') {
    return `${deployUrlPrefix}/vue_project_${appId}/dist/index.html?t=${Date.now()}`
  }
  return `${deployUrlPrefix}/${codeGenType}_${appId}/index.html?t=${Date.now()}`
}

const hasPreviewCandidate = () => {
  const latestAiMessage = [...messages.value].reverse().find((item) => item.role === 'ai')
  if (!latestAiMessage || latestAiMessage.status === 'failed' || looksLikeGenerationFailure(latestAiMessage.content)) {
    return false
  }
  return latestAiMessage.status === 'success' || hasFileWriteSignal(latestAiMessage)
}

const hasLatestGenerationFailure = () => {
  const latestAiMessage = [...messages.value].reverse().find((item) => item.role === 'ai')
  return (
    !!latestAiMessage && (latestAiMessage.status === 'failed' || looksLikeGenerationFailure(latestAiMessage.content))
  )
}

const hasFileWriteSignal = (messageItem: ChatMessage) => {
  if (
    messageItem.toolEvents?.some((eventItem) => eventItem.type === 'executed' && eventItem.text.includes('写入文件'))
  ) {
    return true
  }
  return messageItem.content.includes('[工具完成]') || messageItem.content.includes('已写入文件')
}

const looksLikeGenerationFailure = (content: string) => {
  const lowerContent = content.toLowerCase()
  return (
    lowerContent.includes('the request was rejected') ||
    lowerContent.includes('high risk') ||
    content.includes('[错误]') ||
    content.includes('生成失败：') ||
    content.includes('构建失败：') ||
    content.includes('HTML代码不能为空')
  )
}

const checkPreviewResource = async (url: string) => {
  try {
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include',
      cache: 'no-store',
    })
    if (!response.ok) {
      return false
    }
    const text = await response.text()
    return !(text.includes('Whitelabel Error Page') || text.includes('No static resource'))
  } catch {
    return false
  }
}

const extractLatestFailureReason = () => {
  for (let i = messages.value.length - 1; i >= 0; i -= 1) {
    const item = messages.value[i]
    if (item.role !== 'ai' || !item.content) {
      continue
    }
    const lines = item.content
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .reverse()
    const failureLine = lines.find((line) => {
      return (
        line.startsWith('生成失败：') ||
        line.startsWith('构建失败：') ||
        line.toLowerCase().includes('the request was rejected') ||
        line.toLowerCase().includes('high risk') ||
        line.includes('argument type mismatch')
      )
    })
    if (failureLine) {
      return failureLine
    }
  }
  return ''
}

const isTimeoutFailureReason = (reason: string) => {
  const lowerReason = reason.toLowerCase()
  return lowerReason.includes('timeout') || lowerReason.includes('timed out') || lowerReason.includes('read timed out')
}

const handleIframeLoad = () => {
  if (!iframeRef.value) {
    return
  }
  try {
    const text = iframeRef.value.contentDocument?.body?.innerText || ''
    if (text.includes('Whitelabel Error Page') || text.includes('No static resource')) {
      iframeUrl.value = ''
      previewStatus.value = 'failed'
      const latestFailureReason = extractLatestFailureReason()
      if (latestFailureReason) {
        previewWarning.value = isTimeoutFailureReason(latestFailureReason)
          ? `预览资源不存在，AI 服务响应超时导致本次代码未完整生成。建议重试一次，或先缩短需求范围后再次生成。最近一次失败原因：${latestFailureReason}`
          : `预览资源不存在，通常是中间生成或构建失败导致目标文件未生成。最近一次失败原因：${latestFailureReason}`
      } else {
        previewWarning.value =
          '预览资源不存在，通常是中间生成或构建失败导致目标文件未生成。请先查看最新 AI 消息中的构建结果。'
      }
      return
    }
    previewWarning.value = ''
    previewStatus.value = 'ready'
  } catch {
    previewWarning.value = ''
  }
  visualEditor.handleIframeLoad()
}

const clearSelectedElement = () => {
  selectedElement.value = null
  visualEditor.clearSelection()
}

const toggleEditMode = () => {
  if (!iframeUrl.value) {
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
  if (iframeUrl.value) {
    clearSelectedElement()
    const url = new URL(iframeUrl.value)
    url.searchParams.set('t', Date.now().toString())
    iframeUrl.value = url.toString()
  }
}

const handleCreateSession = async () => {
  if (generating.value) {
    message.warning('正在生成代码，请稍后再新建会话')
    return
  }
  const newSessionId = await createSession()
  if (newSessionId) {
    clearSelectedElement()
    currentSessionId.value = newSessionId
    messages.value = []
    await updatePreview()
  }
}

const handleSwitchSession = async (sessionId?: string | number) => {
  const normalizedSessionId = normalizeId(sessionId)
  if (!normalizedSessionId || generating.value || normalizedSessionId === currentSessionId.value) {
    return
  }
  clearSelectedElement()
  currentSessionId.value = normalizedSessionId
  await loadRemoteHistory(normalizedSessionId)
  await updatePreview()
}

const startRename = (session: API.ChatSessionVO) => {
  editingSessionId.value = normalizeId(session.id)
  editingTitle.value = session.title || ''
  nextTick(() => {
    const input = document.querySelector('.session-edit-input') as HTMLInputElement
    if (input) {
      input.focus()
      input.select()
    }
  })
}

const confirmRename = async (session: API.ChatSessionVO) => {
  const sid = normalizeId(session.id)
  if (editingSessionId.value !== sid) {
    return
  }
  const newTitle = editingTitle.value.trim()
  editingSessionId.value = ''
  if (!newTitle || newTitle === session.title) {
    return
  }
  try {
    const res = await renameSession({ sessionId: session.id as number, title: newTitle })
    if (res.data?.code === 0) {
      session.title = newTitle
      message.success('重命名成功')
    } else {
      message.error('重命名失败，' + (res.data?.message || '请稍后重试'))
    }
  } catch {
    message.error('重命名失败')
  }
}

const confirmDeleteSession = (session: API.ChatSessionVO) => {
  const sid = normalizeId(session.id)
  if (!sid) {
    return
  }
  Modal.confirm({
    title: '确认删除会话',
    content: `确定要删除「${session.title || '未命名会话'}」吗？删除后不可恢复。`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        const res = await deleteSession({ id: session.id as number })
        if (res.data?.code === 0) {
          message.success('会话已删除')
          if (currentSessionId.value === sid) {
            const remaining = sessions.value.filter((s) => normalizeId(s.id) !== sid)
            if (remaining.length > 0 && remaining[0].id) {
              currentSessionId.value = normalizeId(remaining[0].id)
              await loadRemoteHistory(currentSessionId.value)
            } else {
              currentSessionId.value = undefined
              messages.value = []
              const newSessionId = await createSession()
              if (newSessionId) {
                currentSessionId.value = newSessionId
              }
            }
            await updatePreview()
          }
          await loadSessions()
        } else {
          message.error('删除失败，' + (res.data?.message || '请稍后重试'))
        }
      } catch {
        message.error('删除失败')
      }
    },
  })
}

const formatSessionTime = (time?: string) => {
  if (!time) {
    return '暂无消息'
  }
  const date = new Date(time)
  if (Number.isNaN(date.getTime())) {
    return '暂无消息'
  }
  return date.toLocaleString()
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
  if (!appId) return
  versionLoading.value = true
  try {
    const res = await listAppVersions({ appId: Number(appId) })
    if (res.data?.code === 0) {
      versionList.value = res.data?.data || []
    }
  } finally {
    versionLoading.value = false
  }
}

/**
 * 部署应用
 */
const doDeploy = async () => {
  deployLoading.value = true
  try {
    const res = await deployApp({ appId: appId as any })
    if (res.data?.code === 0) {
      message.success('部署成功！地址：' + res.data.data)
      await loadApp()
      pollCoverAfterDeploy()
    } else {
      message.error('部署失败，' + res.data?.message)
    }
  } finally {
    deployLoading.value = false
  }
}

const doDownload = async () => {
  if (!ensureValidAppId()) {
    return
  }
  if (!canDownload.value) {
    message.warning('仅应用创建者可以下载源码')
    return
  }
  downloadLoading.value = true
  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL
    const response = await fetch(`${baseUrl}/app/download/${appId}`, {
      method: 'GET',
      credentials: 'include',
    })
    if (!response.ok) {
      message.error('下载失败，请稍后重试')
      return
    }
    const contentDisposition = response.headers.get('Content-Disposition') || ''
    const fileNameMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
    const fileName = fileNameMatch?.[1] ? decodeURIComponent(fileNameMatch[1]) : `app-${appId}.zip`
    const blob = await response.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(blobUrl)
    message.success('源码下载已开始')
  } catch (error: any) {
    message.error('下载失败，' + (error?.message || '未知错误'))
  } finally {
    downloadLoading.value = false
  }
}

const formatCodeGenType = (codeGenType?: string) => {
  if (codeGenType === 'single_file') {
    return '单文件模式'
  }
  if (codeGenType === 'multi-file') {
    return '多文件模式'
  }
  if (codeGenType === 'vue_project') {
    return 'Vue 项目模式'
  }
  return codeGenType || '未知模式'
}

const formatCoverTaskStatus = (status?: string, retryCount?: number) => {
  if (status === 'PENDING') {
    return '封面任务待执行'
  }
  if (status === 'RUNNING') {
    return `封面生成中（第 ${retryCount || 1} 次）`
  }
  if (status === 'SUCCESS') {
    return '封面已更新'
  }
  if (status === 'SKIPPED') {
    return '已保留原封面'
  }
  if (status === 'FAILED') {
    return `封面生成失败（重试 ${retryCount || 0} 次）`
  }
  return '封面状态未知'
}

const coverTaskStatusColor = (status?: string) => {
  if (status === 'PENDING') {
    return 'gold'
  }
  if (status === 'RUNNING') {
    return 'processing'
  }
  if (status === 'SUCCESS') {
    return 'success'
  }
  if (status === 'SKIPPED') {
    return 'default'
  }
  if (status === 'FAILED') {
    return 'error'
  }
  return 'default'
}

const pollCoverAfterDeploy = async () => {
  let count = 0
  const maxCount = 8
  const timer = setInterval(async () => {
    count += 1
    await loadApp()
    if (app.value?.cover || app.value?.coverTaskStatus === 'FAILED' || count >= maxCount) {
      if (app.value?.coverTaskStatus === 'FAILED' && app.value?.coverErrorMessage) {
        message.warning(`封面生成失败：${app.value.coverErrorMessage}`)
      }
      clearInterval(timer)
    }
  }, 4000)
}

const renderMarkdown = (text: string) => {
  return text
    .replace(/\n/g, '<br/>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

const parseAiMessage = (
  content: string,
  presetToolEvents: ToolEvent[] = [],
): { aiText: string; toolEvents: ToolEvent[] } => {
  if (presetToolEvents.length > 0) {
    return {
      aiText: stripToolEventLines(content).trim(),
      toolEvents: presetToolEvents,
    }
  }
  const lines = content.split('\n')
  const aiTextLines: string[] = []
  const toolEvents: ToolEvent[] = []

  lines.forEach((line) => {
    const trimmedLine = line.trim()
    if (trimmedLine.startsWith('[工具调用]')) {
      toolEvents.push({
        type: 'request',
        text: trimmedLine.replace('[工具调用]', '').trim() || '执行工具调用',
      })
      return
    }
    if (trimmedLine.startsWith('[工具完成]')) {
      toolEvents.push({
        type: 'executed',
        text: trimmedLine.replace('[工具完成]', '').trim() || '工具执行成功',
      })
      return
    }
    if (trimmedLine.startsWith('准备写入文件')) {
      toolEvents.push({
        type: 'request',
        text: trimmedLine,
      })
      return
    }
    if (trimmedLine.startsWith('已写入文件')) {
      toolEvents.push({
        type: 'executed',
        text: trimmedLine,
      })
      return
    }
    aiTextLines.push(line)
  })

  return {
    aiText: aiTextLines.join('\n').trim(),
    toolEvents,
  }
}

const stripToolEventLines = (content: string) => {
  return content
    .split('\n')
    .filter((line) => {
      const trimmedLine = line.trim()
      return !(
        trimmedLine.startsWith('[工具调用]') ||
        trimmedLine.startsWith('[工具完成]') ||
        trimmedLine.startsWith('准备写入文件') ||
        trimmedLine.startsWith('已写入文件')
      )
    })
    .join('\n')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

watch(showVersionPanel, (val) => {
  if (val) loadVersions()
})

onMounted(() => {
  const backPath = (window.history.state?.back as string | undefined) || ''
  const forwardPath = (window.history.state?.forward as string | undefined) || ''
  if (backPath && !backPath.includes('/app/generate/')) {
    sessionStorage.setItem(entryPathStorageKey, backPath)
  }

  const navigationEntries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[]
  const navigationType = navigationEntries[0]?.type || ''
  const entryPath = sessionStorage.getItem(entryPathStorageKey) || ''
  if (navigationType === 'back_forward' && forwardPath.includes('/app/generate/') && entryPath) {
    router.replace(entryPath)
    return
  }

  loadApp()
})

const handleBack = async () => {
  const targetPath = sessionStorage.getItem(entryPathStorageKey) || '/app/my'
  await router.replace(targetPath)
}

const resizePanel = (event: MouseEvent) => {
  if (!resizing.value) {
    return
  }
  const deltaX = event.clientX - resizeStartX.value
  const nextWidth = resizeStartWidth.value + deltaX
  const minWidth = 320
  const maxWidth = Math.floor(window.innerWidth * 0.7)
  chatPanelWidth.value = Math.max(minWidth, Math.min(nextWidth, maxWidth))
}

const stopResize = () => {
  resizing.value = false
  document.body.style.userSelect = ''
  window.removeEventListener('mousemove', resizePanel)
  window.removeEventListener('mouseup', stopResize)
}

const startResize = (event: MouseEvent) => {
  resizing.value = true
  resizeStartX.value = event.clientX
  resizeStartWidth.value = chatPanelWidth.value
  document.body.style.userSelect = 'none'
  window.addEventListener('mousemove', resizePanel)
  window.addEventListener('mouseup', stopResize)
}

onUnmounted(() => {
  visualEditor.exitEditMode()
  visualEditor.dispose()
  stopResize()
})
</script>

<style scoped>
#appGeneratorPage {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-background);
}

.top-nav {
  height: 56px;
  padding: 0 20px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface);
}

.app-name {
  font-weight: 600;
  font-size: 16px;
  margin-left: 8px;
  color: var(--color-text);
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 对话面板 */
.chat-panel {
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  min-width: 320px;
  max-width: 70vw;
  flex-shrink: 0;
}

.panel-splitter {
  width: 8px;
  cursor: col-resize;
  background: transparent;
  transition: background 0.2s;
  flex-shrink: 0;
}

.panel-splitter:hover {
  background: var(--color-border);
}

.session-panel {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
}

.session-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.session-list {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.session-item {
  min-width: 140px;
  max-width: 180px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 8px 10px;
  cursor: pointer;
  transition: all var(--transition-normal);
  background: var(--color-surface);
  position: relative;
}

.session-item:hover {
  border-color: var(--color-border-light);
}

.session-item:hover .session-actions {
  opacity: 1;
}

.session-item.active {
  border-color: var(--color-cta);
  background: var(--color-surface-elevated);
}

.session-title {
  font-size: 13px;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-edit-input {
  font-size: 13px;
  color: var(--color-text);
  background: var(--color-background);
  border: 1px solid var(--color-cta);
  border-radius: 4px;
  padding: 2px 6px;
  width: 100%;
  outline: none;
}

.session-time {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-actions {
  position: absolute;
  top: 4px;
  right: 4px;
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.session-action-btn {
  color: var(--color-text-muted) !important;
  font-size: 12px !important;
}

.session-action-btn:hover {
  color: var(--color-cta) !important;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.user-msg {
  flex-direction: row-reverse;
}

.message-body {
  max-width: 80%;
}

.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.message-text {
  white-space: normal;
}

.user-msg .message-content {
  background: var(--color-surface-elevated);
  color: var(--color-text);
}

.ai-msg .message-content {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  color: var(--color-text);
}

.tool-call-card {
  margin-top: 10px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: var(--color-surface);
  overflow: hidden;
}

.tool-call-summary {
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
}

.tool-call-summary::-webkit-details-marker {
  display: none;
}

.tool-call-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
}

.tool-call-hint {
  font-size: 12px;
  color: var(--color-text-muted);
}

.tool-call-list {
  border-top: 1px solid var(--color-border);
  background: var(--color-background);
}

.tool-call-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
}

.tool-call-item:last-child {
  border-bottom: none;
}

.tool-call-tag {
  flex-shrink: 0;
  font-size: 11px;
  line-height: 1;
  padding: 5px 7px;
  border-radius: 99px;
  border: 1px solid transparent;
}

.tool-call-tag.request {
  color: var(--color-info);
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
}

.tool-call-tag.executed {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.3);
}

.tool-call-text {
  font-size: 13px;
  color: var(--color-text-secondary);
  word-break: break-all;
}

.generating-indicator {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: -12px;
  margin-left: 44px;
}

.workflow-steps {
  margin-top: 12px;
  margin-left: 44px;
  padding: 12px;
  background: var(--color-surface-elevated);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.workflow-steps-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.workflow-steps-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.workflow-step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.workflow-step-item.running {
  color: var(--color-info);
}

.workflow-step-item.completed {
  color: var(--color-success);
}

.workflow-step-item.error {
  color: var(--color-error);
}

.workflow-step-icon {
  font-size: 14px;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.workflow-step-content {
  flex: 1;
}

.workflow-step-name {
  font-weight: 500;
}

.workflow-step-error {
  font-size: 11px;
  color: var(--color-error);
  margin-top: 2px;
}

.stream-warning {
  padding: 0 20px 12px;
}

.stream-warning :deep(.ant-alert) {
  border-radius: 10px;
}

.selected-element-panel {
  padding: 0 20px 12px;
}

.selected-element-panel :deep(.ant-alert) {
  border-radius: 10px;
}

.selected-element-content {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
  word-break: break-all;
}

.input-area {
  padding: 20px;
  border-top: 1px solid var(--color-border);
}

.input-wrapper {
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 8px;
  transition: all 0.3s;
  background: var(--color-background);
}

.input-wrapper:focus-within {
  border-color: var(--color-cta);
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.15);
}

.input-wrapper :deep(textarea) {
  border: none !important;
  box-shadow: none !important;
  padding: 8px 12px;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

/* 预览面板 */
.preview-panel {
  flex: 1;
  background: var(--color-background);
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow: hidden;
  position: relative;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.preview-warning {
  margin-bottom: 12px;
  border-radius: 10px;
}

.preview-body {
  flex: 1;
  background: var(--color-surface);
  border-radius: 12px;
  box-shadow: var(--shadow-md);
  overflow: hidden;
  position: relative;
  transition: all 0.3s;
  height: 0;
}

.preview-body.mobile {
  max-width: 375px;
  margin: 0 auto;
  height: 667px;
  flex: none;
}

.preview-iframe {
  width: 100%;
  height: 100%;
}

.preview-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.empty-content {
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.deploy-btn {
  border-radius: 20px;
  background: var(--color-cta);
  border-color: var(--color-cta);
}

.deploy-btn:hover {
  background: var(--color-cta-hover) !important;
  border-color: var(--color-cta-hover) !important;
}

.download-btn {
  border-radius: 20px;
}

.version-panel {
  position: absolute;
  top: 40px;
  right: 8px;
  width: 260px;
  max-height: 360px;
  background: var(--color-bg-elevated, #1e293b);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  z-index: 20;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.version-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary, #f1f5f9);
}

.version-panel-body {
  overflow-y: auto;
  padding: 8px;
  flex: 1;
}

.version-loading,
.version-empty {
  text-align: center;
  padding: 24px 0;
  color: var(--color-text-tertiary, #94a3b8);
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
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  transition: background 0.15s;
}

.version-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.version-no {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-cta, #22c55e);
}

.version-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.version-status {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(34, 197, 94, 0.12);
  color: #22c55e;
}

.version-time {
  font-size: 11px;
  color: var(--color-text-tertiary, #94a3b8);
}
</style>
