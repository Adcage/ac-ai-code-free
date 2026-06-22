import { ref, isRef, unref, type Ref } from 'vue'
import { message } from 'ant-design-vue'

export interface ToolEvent {
  type: 'request' | 'executed' | 'status'
  text: string
}

export interface PlanningOption {
  id?: string
  value?: string
  label: string
  description?: string
  recommended?: boolean
}

export interface PlanningQuestion {
  id: string
  prompt?: string
  question?: string
  inputType: 'single_select' | 'multi_select'
  required: boolean
  options?: PlanningOption[]
  reason?: string
  placeholder?: string
}

export interface PlanningQuestionSet {
  questionSetId: string
  stage?: string
  protocolVersion?: number
  questions: PlanningQuestion[]
}

export interface ChatMessage {
  role: 'user' | 'ai'
  content: string
  status?: string
  toolEvents?: ToolEvent[]
  planning?: PlanningQuestionSet
}

export interface SSEChatOptions {
  appId: string | Ref<string>
  messages: Ref<ChatMessage[]>
  onPreviewUpdate: () => void
  onSessionsUpdate?: () => void
  onAppUpdate?: (data: { codeGenType?: string }) => void
}

/**
 * SSE 流式对话 composable
 * 封装 EventSource 连接管理、消息流解析、工具调用事件处理
 */
export function useSSEChat(options: SSEChatOptions) {
  const { appId, messages, onPreviewUpdate, onSessionsUpdate, onAppUpdate } = options

  const generating = ref(false)
  const streamWarning = ref('')
  let currentEventSource: EventSource | null = null
  let previewUpdateTimer: ReturnType<typeof setTimeout> | null = null

  const normalizeId = (id?: string | number | null) => {
    if (id === undefined || id === null) return ''
    return String(id)
  }

  const startSSE = (userMsg: string, sessionId: string, codeGenType?: string) => {
    generating.value = true
    streamWarning.value = ''
    let streamCompleted = false
    const aiMsgIndex = messages.value.length
    messages.value.push({ role: 'ai', content: '', status: 'running' })

    const isStructuredToolMode =
      codeGenType === 'vue_project' || codeGenType === 'multi-file' || codeGenType === 'single_file'

    const baseUrl = import.meta.env.VITE_API_BASE_URL
    const eventSource = new EventSource(
      `${baseUrl}/app/chat/gen/code/stream?appId=${unref(appId)}&sessionId=${sessionId}&message=${encodeURIComponent(userMsg)}`,
      { withCredentials: true },
    )
    currentEventSource = eventSource

    eventSource.addEventListener('meta', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        // meta 事件暂不做特殊处理
        void data
      } catch (e) {
        console.error('SSE Meta Parse Error', e)
      }
    })

    const stopGenerating = (delayPreviewRefresh = false) => {
      eventSource.close()
      currentEventSource = null
      if (streamCompleted) {
        streamWarning.value = ''
      }
      if (generating.value) {
        generating.value = false
        onSessionsUpdate?.()
        if (delayPreviewRefresh) {
          setTimeout(() => {
            messages.value[aiMsgIndex].status = streamCompleted ? 'success' : 'failed'
            onPreviewUpdate()
          }, 500)
        } else {
          messages.value[aiMsgIndex].status = streamCompleted ? 'success' : 'failed'
          onPreviewUpdate()
        }
      }
    }

    eventSource.addEventListener('business-error', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        const errorMsg = data.message || '操作失败'
        messages.value[aiMsgIndex].content += `\n\n[错误] ${errorMsg}`
        messages.value[aiMsgIndex].status = 'failed'
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
      } catch {
        if (rawData.includes('[DONE]')) {
          streamCompleted = true
          stopGenerating(true)
        }
      }
    }

    eventSource.onerror = () => {
      if (!streamCompleted) {
        streamWarning.value = '连接中断，本次 AI 输出可能未完整保存。可重新加载当前会话查看已落库内容。'
        messages.value[aiMsgIndex].status = 'failed'
        message.warning('连接中断，已停止本次生成')
      }
      stopGenerating()
    }
  }

  const stopSSE = () => {
    if (currentEventSource) {
      currentEventSource.close()
      currentEventSource = null
    }
    generating.value = false
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
        const data = messageObj.data || ''
        if (data !== 'waiting_for_user') {
          messages.value[aiMsgIndex].content += data
        }
        return
      }
      if (type === 'tool_request') {
        if (messageObj.name === 'ask_user') {
          const payload = parseAskUserStructuredPayload(messageObj.arguments)
          if (!payload) return
          const targetMessage = messages.value[aiMsgIndex]
          if (!targetMessage.planning || targetMessage.planning.questionSetId !== payload.questionSetId) {
            targetMessage.planning = payload
            // 同步生成一段简短说明文本，保持旧 <planning> 标签的兼容
            targetMessage.content += `\n<planning type="clarification">${JSON.stringify({
              questions: payload.questions.map((q) => ({
                id: q.id,
                question: q.prompt,
                inputType: q.inputType,
                required: q.required,
                options: (q.options || []).map((o) => ({
                  value: o.id,
                  label: o.label,
                  recommended: o.recommended,
                })),
              })),
            })}</planning>\n`
          }
          return
        }
        const text = formatToolText(messageObj.name, messageObj.arguments, 'request')
        appendToolEvent(aiMsgIndex, { type: 'request', text })
        return
      }
      if (type === 'tool_executed') {
        if (messageObj.name === 'ask_user') return
        const executedText = formatToolText(messageObj.name, messageObj.arguments, 'executed', messageObj.result)
        appendToolEvent(aiMsgIndex, { type: 'executed', text: executedText })
        return
      }
      if (type === 'status') {
        const statusText = messageObj.message || '处理中...'
        appendToolEvent(aiMsgIndex, { type: 'status', text: statusText })
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
    if (!targetMessage) return
    if (!targetMessage.toolEvents) {
      targetMessage.toolEvents = []
    }
    targetMessage.toolEvents.push(eventItem)
    // 工具执行完成 → 文件可能已变化，防抖触发预览检查
    if (eventItem.type === 'executed') {
      if (previewUpdateTimer) clearTimeout(previewUpdateTimer)
      previewUpdateTimer = setTimeout(() => {
        onPreviewUpdate()
        previewUpdateTimer = null
      }, 2000)
    }
  }

  const parseAskUserStructuredPayload = (
    argumentsData?: string | Record<string, unknown>,
  ): PlanningQuestionSet | null => {
    if (!argumentsData) return null
    try {
      let argsObj: Record<string, unknown>
      if (typeof argumentsData === 'string') {
        argsObj = JSON.parse(argumentsData)
      } else {
        argsObj = argumentsData
      }
      const questionSetId =
        (argsObj.questionSetId as string) ||
        ((argsObj.questions as Array<{ id?: string }> | undefined)?.[0]?.id ?? 'qs_legacy')
      const stage = (argsObj.stage as string) || ''
      const protocolVersion = Number(argsObj.protocolVersion || 1)
      const rawQuestions = Array.isArray(argsObj.questions) ? (argsObj.questions as Array<Record<string, unknown>>) : []
      const questions: PlanningQuestion[] = rawQuestions.map((q) => {
        const promptText = String(q.prompt || q.question || '')
        // 兜底归一化 inputType：协议值是 single_select / multi_select。
        // 后端已对非法值归一化并拒绝 text，但前端再做一次防御，
        // 防止后端漏处理时直接把 single_choice / select 等变体显示成"无选项"。
        const rawInputType = String(q.inputType || '').toLowerCase()
        let inputType: PlanningQuestion['inputType']
        if (rawInputType === 'multi_select' || rawInputType === 'multi' || rawInputType === 'multiple' || rawInputType.includes('multi')) {
          inputType = 'multi_select'
        } else {
          inputType = 'single_select'
        }
        return {
          id: String(q.id || ''),
          prompt: promptText,
          question: promptText,
          inputType,
          required: q.required !== false,
          reason: (q.reason as string) || '',
          placeholder: (q.placeholder as string) || '',
          options: Array.isArray(q.options)
            ? (q.options as Array<Record<string, unknown>>).map((opt) => ({
                id: String(opt.id || opt.value || opt.label || ''),
                label: String(opt.label || opt.id || opt.value || ''),
                description: (opt.description as string) || '',
                recommended: Boolean(opt.recommended),
              }))
            : [],
        }
      })
      return { questionSetId, stage, protocolVersion, questions }
    } catch (e) {
      console.warn('[ask_user] parseAskUserStructuredPayload failed', argumentsData, e)
      return null
    }
  }

  const parseAskUserArgs = (argumentsData?: string | Record<string, unknown>) => {
    const payload = parseAskUserStructuredPayload(argumentsData)
    if (!payload) return null
    const first = payload.questions[0]
    if (!first) return null
    return {
      question: first.prompt,
      inputType: first.inputType,
      options: (first.options || []).map((o) => o.id),
    }
  }

  const handleWorkflowEvent = (eventData: Record<string, unknown>, _aiMsgIndex: number) => {
    const eventType = eventData.event as string
    const data = (eventData.data || {}) as Record<string, unknown>

    if (eventType === 'workflow_completed') {
      onAppUpdate?.({ codeGenType: data.codeGenType as string | undefined })
    }
  }

  const parsePathFromArguments = (argumentsText?: string) => {
    if (!argumentsText) return ''
    try {
      const argsObj = JSON.parse(argumentsText)
      return argsObj.relative_path || argsObj.relativeFilePath || argsObj.relative_dir_path || argsObj.relativeDirPath || ''
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
      write_file: path ? `准备写入文件 ${path}` : '准备写入文件',
      writeFile: path ? `准备写入文件 ${path}` : '准备写入文件',
      read_file: path ? `准备读取文件 ${path}` : '准备读取文件',
      readFile: path ? `准备读取文件 ${path}` : '准备读取文件',
      modify_file: path ? `准备修改文件 ${path}` : '准备修改文件',
      modifyFile: path ? `准备修改文件 ${path}` : '准备修改文件',
      delete_file: path ? `准备删除文件 ${path}` : '准备删除文件',
      deleteFile: path ? `准备删除文件 ${path}` : '准备删除文件',
      read_dir: path ? `准备读取目录 ${path}` : '准备读取目录结构',
      readDir: path ? `准备读取目录 ${path}` : '准备读取目录结构',
      read_asset: '准备读取资源文件',
      run_command: '正在执行终端命令',
    }
    const executedMap: Record<string, string> = {
      write_file: path ? `已写入文件 ${path}` : '文件写入成功',
      writeFile: path ? `已写入文件 ${path}` : '文件写入成功',
      read_file: path ? `已读取文件 ${path}` : '文件读取成功',
      readFile: path ? `已读取文件 ${path}` : '文件读取成功',
      modify_file: path ? `已修改文件 ${path}` : '文件修改成功',
      modifyFile: path ? `已修改文件 ${path}` : '文件修改成功',
      delete_file: path ? `已删除文件 ${path}` : '文件删除成功',
      deleteFile: path ? `已删除文件 ${path}` : '文件删除成功',
      read_dir: path ? `目录结构读取完成 ${path}` : '目录结构读取完成',
      readDir: path ? `目录结构读取完成 ${path}` : '目录结构读取完成',
      read_asset: '资源文件读取完成',
      run_command: '终端命令执行完成',
    }
    if (stage === 'request') {
      return requestMap[toolName || ''] || `正在执行 ${toolName || '工具'}`
    }
    // 已知错误消息原样展示
    if (result && (String(result).startsWith('文件修改失败') || String(result).startsWith('禁止删除关键文件'))) {
      return result
    }
    // 优先用映射，否则显示简短摘要（不展示原始 result，避免文件内容刷屏）
    return executedMap[toolName || ''] || `已执行 ${toolName || '工具'}`
  }

  return {
    generating,
    streamWarning,
    startSSE,
    stopSSE,
  }
}
