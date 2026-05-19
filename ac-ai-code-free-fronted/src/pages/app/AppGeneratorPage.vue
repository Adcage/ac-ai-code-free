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
            <a-button type="link" size="small" :loading="sessionLoading" @click="handleCreateSession">新建会话</a-button>
          </div>
          <div class="session-list">
            <div
              v-for="(session, index) in sessions"
              :key="session.id || index"
              :class="['session-item', normalizeId(session.id) === currentSessionId ? 'active' : '']"
              @click="handleSwitchSession(session.id)"
            >
              <div class="session-title">{{ session.title || `会话 ${index + 1}` }}</div>
              <div class="session-time">{{ formatSessionTime(session.lastMessageTime) }}</div>
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
                  <template v-for="parsed in [parseAiMessage(msg.content, msg.toolEvents || [])]" :key="`parsed-${index}`">
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
                  </template>
                </template>
                <div v-else class="message-text" v-html="renderMarkdown(msg.content)"></div>
              </div>
            </div>
          </div>
          <div v-if="generating" class="generating-indicator">
            <loading-outlined /> AI 正在思考并生成代码...
          </div>
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
                <a-button type="text" size="small"><template #icon><paper-clip-outlined /></template>上传</a-button>
                <a-button type="text" size="small"><template #icon><thunderbolt-outlined /></template>优化</a-button>
              </a-space>
              <a-button 
                type="primary" 
                shape="circle" 
                size="small" 
                :disabled="generating || !inputText" 
                @click="doChat"
              >
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
            <a-button size="small" :type="editMode ? 'primary' : 'default'" @click="toggleEditMode">
              {{ editMode ? '退出编辑模式' : '进入编辑模式' }}
            </a-button>
            <a-button size="small" :disabled="!selectedElement" @click="clearSelectedElement">清除选中</a-button>
            <a-button size="small" @click="refreshIframe">
              <template #icon><reload-outlined /></template>
            </a-button>
          </a-space>
        </div>
        <a-alert
          v-if="previewWarning"
          class="preview-warning"
          type="warning"
          show-icon
          :message="previewWarning"
        />
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
              <p>应用生成中，完成后将在此展示效果</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  LeftOutlined,
  CloudUploadOutlined,
  DownloadOutlined,
  ReloadOutlined,
  PaperClipOutlined, 
  ThunderboltOutlined, 
  ArrowUpOutlined,
  LoadingOutlined
} from '@ant-design/icons-vue'
import { createChatSession, deployApp, getAppVoById, listChatHistoryByPage, listChatSession } from '@/api/appController'
import { useLoginUserStore } from '@/stores/LoginUser'
import { createVisualEditor, type ElementInfo } from '@/utils/visualEditor'

const route = useRoute()
const router = useRouter()
const loginUserStore = useLoginUserStore()
const appId = String(route.params.id ?? '')

const app = ref<API.AppVO>()
const messages = ref<{ role: 'user' | 'ai', content: string, toolEvents?: ToolEvent[] }[]>([])
const sessions = ref<API.ChatSessionVO[]>([])
const currentSessionId = ref<string>()
const inputText = ref('')
const generating = ref(false)
const deployLoading = ref(false)
const downloadLoading = ref(false)
const sessionLoading = ref(false)
const sessionInitializing = ref(false)
const previewType = ref('desktop')
const iframeUrl = ref('')
const iframeRef = ref<HTMLIFrameElement>()
const messageListRef = ref<HTMLElement>()
const streamWarning = ref('')
const previewWarning = ref('')
const entryPathStorageKey = `app_generate_entry_${appId}`
const chatPanelWidth = ref(450)
const resizing = ref(false)
const resizeStartX = ref(0)
const resizeStartWidth = ref(450)
const selectedElement = ref<ElementInfo | null>(null)
const editMode = ref(false)

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
      updatePreview()
    } else {
      const newSessionId = await createSession()
      if (newSessionId) {
        currentSessionId.value = newSessionId
      }
      if (app.value?.initPrompt && currentSessionId.value) {
        messages.value.push({ role: 'user', content: app.value.initPrompt, toolEvents: [] })
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
  let streamCompleted = false
  const aiMsgIndex = messages.value.length
  messages.value.push({ role: 'ai', content: '' })
  const isVueProjectMode = app.value?.codeGenType === 'vue_project'

  const baseUrl = import.meta.env.VITE_API_BASE_URL
  const eventSource = new EventSource(
    `${baseUrl}/app/chat/gen/code/stream?appId=${appId}&sessionId=${sessionId}&message=${encodeURIComponent(userMsg)}`,
    { withCredentials: true }
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

  const stopGenerating = () => {
    eventSource.close()
    if (streamCompleted) {
      streamWarning.value = ''
    }
    if (generating.value) {
      generating.value = false
      loadSessions()
      updatePreview()
    }
  }

  eventSource.addEventListener('done', () => {
    streamCompleted = true
    stopGenerating()
  })

  eventSource.onmessage = (event) => {
    const rawData = event.data
    if (rawData === '[DONE]') {
      streamCompleted = true
      stopGenerating()
      return
    }
    
    try {
      const data = JSON.parse(rawData)
      if (data.d === '[DONE]') {
        streamCompleted = true
        stopGenerating()
        return
      }
      const chunk = data.d || ''
      if (!isVueProjectMode) {
        messages.value[aiMsgIndex].content += chunk
      } else {
        appendVueProjectChunk(aiMsgIndex, chunk)
      }
      scrollToBottom()
    } catch {
      if (rawData.includes('[DONE]')) {
        streamCompleted = true
        stopGenerating()
      }
    }
  }

  eventSource.onerror = (err) => {
    console.error('SSE Error', err)
    if (!streamCompleted) {
      streamWarning.value = '连接中断，本次 AI 输出可能未完整保存。可重新加载当前会话查看已落库内容。'
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

const appendVueProjectChunk = (aiMsgIndex: number, chunk: string) => {
  try {
    const messageObj = JSON.parse(chunk)
    const type = messageObj.type
    if (type === 'ai_response') {
      messages.value[aiMsgIndex].content += messageObj.data || ''
      return
    }
    if (type === 'tool_request') {
      const text = `\n[工具调用] ${formatToolText(messageObj.name, messageObj.arguments, 'request')}`
      messages.value[aiMsgIndex].content += text
      return
    }
    if (type === 'tool_executed') {
      const executedText = formatToolText(messageObj.name, messageObj.arguments, 'executed', messageObj.result)
      const text = `\n[工具完成] ${executedText}`
      messages.value[aiMsgIndex].content += text
      return
    }
    messages.value[aiMsgIndex].content += chunk
  } catch {
    messages.value[aiMsgIndex].content += chunk
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

const formatToolText = (toolName?: string, argumentsText?: string, stage: 'request' | 'executed' = 'request', result?: string) => {
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
  return executedMap[toolName || ''] || (result || `工具执行成功 ${toolName || ''}`.trim())
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
  messages.value.push({ role: 'user', content: rawMessage, toolEvents: [] })
  inputText.value = ''
  startSSE(promptMessage, sessionId)
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
const updatePreview = () => {
  const codeGenType = app.value?.codeGenType || 'single_file'
  const deployUrlPrefix = import.meta.env.VITE_APP_DEPLOY_URL_PREFIX
  previewWarning.value = ''
  selectedElement.value = null
  if (codeGenType === 'vue_project') {
    iframeUrl.value = `${deployUrlPrefix}/vue_project_${appId}/dist/index.html?t=${Date.now()}`
    return
  }
  iframeUrl.value = `${deployUrlPrefix}/${codeGenType}_${appId}/index.html?t=${Date.now()}`
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
      const latestFailureReason = extractLatestFailureReason()
      if (latestFailureReason) {
        previewWarning.value = isTimeoutFailureReason(latestFailureReason)
          ? `预览资源不存在，AI 服务响应超时导致本次代码未完整生成。建议重试一次，或先缩短需求范围后再次生成。最近一次失败原因：${latestFailureReason}`
          : `预览资源不存在，通常是中间生成或构建失败导致目标文件未生成。最近一次失败原因：${latestFailureReason}`
      } else {
        previewWarning.value = '预览资源不存在，通常是中间生成或构建失败导致目标文件未生成。请先查看最新 AI 消息中的构建结果。'
      }
      return
    }
    previewWarning.value = ''
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
    updatePreview()
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

const parseAiMessage = (content: string, presetToolEvents: ToolEvent[] = []): { aiText: string; toolEvents: ToolEvent[] } => {
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
  background: #fdfdfd;
}

.top-nav {
  height: 56px;
  padding: 0 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
}

.app-name {
  font-weight: 600;
  font-size: 16px;
  margin-left: 8px;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 对话面板 */
.chat-panel {
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  background: #fff;
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
  background: #f0f0f0;
}

.session-panel {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.session-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  color: #595959;
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
  border: 1px solid #e8e8e8;
  border-radius: 10px;
  padding: 8px 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.session-item:hover {
  border-color: #d9d9d9;
}

.session-item.active {
  border-color: #1a1a1a;
  background: #fafafa;
}

.session-title {
  font-size: 13px;
  color: #1f1f1f;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  margin-top: 4px;
  font-size: 12px;
  color: #8c8c8c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
  background: #f5f5f5;
  color: #1a1a1a;
}

.ai-msg .message-content {
  background: #fff;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.tool-call-card {
  margin-top: 10px;
  border: 1px solid #e7e9ee;
  border-radius: 10px;
  background: #f8fafc;
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
  color: #1f2937;
}

.tool-call-hint {
  font-size: 12px;
  color: #6b7280;
}

.tool-call-list {
  border-top: 1px solid #e7e9ee;
  background: #fff;
}

.tool-call-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
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
  color: #1d4ed8;
  background: #dbeafe;
  border-color: #bfdbfe;
}

.tool-call-tag.executed {
  color: #047857;
  background: #d1fae5;
  border-color: #a7f3d0;
}

.tool-call-text {
  font-size: 13px;
  color: #374151;
  word-break: break-all;
}

.generating-indicator {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: -12px;
  margin-left: 44px;
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
  color: #334155;
  word-break: break-all;
}

.input-area {
  padding: 20px;
  border-top: 1px solid #f0f0f0;
}

.input-wrapper {
  border: 1px solid #e8e8e8;
  border-radius: 16px;
  padding: 8px;
  transition: all 0.3s;
}

.input-wrapper:focus-within {
  border-color: #1a1a1a;
  box-shadow: 0 0 0 2px rgba(0,0,0,0.02);
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
  background: #f7f8fa;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow: hidden;
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
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  overflow: hidden;
  position: relative;
  transition: all 0.3s;
  height: 0; /* 强制子元素计算高度 */
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
  color: #bfbfbf;
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
  background: #1a1a1a;
  border-color: #1a1a1a;
}

.download-btn {
  border-radius: 20px;
}
</style>
