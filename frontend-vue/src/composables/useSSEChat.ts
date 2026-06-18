import { ref, isRef, unref, type Ref } from 'vue'
import { message } from 'ant-design-vue'

export interface ToolEvent {
  type: 'request' | 'executed' | 'status'
  text: string
}

export interface ChatMessage {
  role: 'user' | 'ai'
  content: string
  status?: string
  toolEvents?: ToolEvent[]
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
          const args = parseAskUserArgs(messageObj.arguments)
          if (!args) return
          const inputType = args.inputType || 'text_input'
          if (inputType === 'text_input') {
            messages.value[aiMsgIndex].content += `\n\n**${args.question}**`
          } else {
            const planningJson = JSON.stringify({
              questions: [
                {
                  id: 'q1',
                  question: args.question,
                  inputType,
                  required: true,
                  options: (args.options || []).map((o: string) => ({ value: o, label: o })),
                },
              ],
            })
            messages.value[aiMsgIndex].content += `\n<planning type="clarification">${planningJson}</planning>\n`
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
  }

  const parseAskUserArgs = (argumentsData?: string | Record<string, unknown>) => {
    if (!argumentsData) return null
    try {
      let argsObj: Record<string, unknown>
      if (typeof argumentsData === 'string') {
        argsObj = JSON.parse(argumentsData)
      } else {
        argsObj = argumentsData
      }
      return {
        question: (argsObj.question as string) || '',
        inputType: (argsObj.input_type as string) || (argsObj.inputType as string) || 'text_input',
        options: Array.isArray(argsObj.options) ? (argsObj.options as string[]) : [],
      }
    } catch (e) {
      if (typeof argumentsData === 'string') {
        try {
          const normalized = argumentsData.trim().replace(/'/g, '"')
          const argsObj = JSON.parse(normalized)
          return {
            question: (argsObj.question as string) || '',
            inputType: (argsObj.input_type as string) || (argsObj.inputType as string) || 'text_input',
            options: Array.isArray(argsObj.options) ? (argsObj.options as string[]) : [],
          }
        } catch {
          // fall through
        }
      }
      console.warn('[ask_user] parseAskUserArgs failed', argumentsData, e)
      return null
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
    if (result && String(result).startsWith('文件修改失败')) return result
    if (result && String(result).startsWith('禁止删除关键文件')) return result
    return executedMap[toolName || ''] || result || `工具执行成功 ${toolName || ''}`.trim()
  }

  return {
    generating,
    streamWarning,
    startSSE,
    stopSSE,
  }
}
