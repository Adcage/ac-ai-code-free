/**
 * 应用预览 Composable
 *
 * 封装了 SSE 对话 + 预览刷新的通用逻辑，
 * 供 AppGeneratorPage 和 TestChatPage 复用。
 *
 * 使用方只需传入 app 数据 ref 和必要参数，
 * 生成完成后自动刷新 app 数据并触发预览更新。
 */
import { ref, unref, type Ref } from 'vue'
import { getAppVoById } from '@/api/appController'
import { useSSEChat, type ChatMessage, type ToolEvent } from './useSSEChat'

export type PreviewStatus = 'idle' | 'generating' | 'checking' | 'ready' | 'failed'

export interface AppPreviewOptions {
  appId: string | Ref<string>
  messages: Ref<ChatMessage[]>
  sessions: Ref<unknown[]>
  loadSessions: () => void | Promise<void>
  /** SSEChat 的 onAppUpdate 回调 */
  onAppUpdate?: (data: { codeGenType?: string }) => void
}

export function useAppPreview(
  appRef: Ref<API.AppVO | undefined>,
  options: AppPreviewOptions,
) {
  // ======== 预览状态 ========
  const iframeUrl = ref('')
  const previewWarning = ref('')
  const previewStatus = ref<PreviewStatus>('idle')

  // ======== app 数据刷新 ========
  const refreshAppData = async () => {
    const appId = unref(options.appId)
    if (!appId) return
    const res = await getAppVoById({ id: appId as any })
    if (res.data?.code === 0) {
      appRef.value = res.data.data
    }
  }

  // ======== 预览刷新 ========
  const checkPreviewResource = async (url: string) => {
    try {
      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        cache: 'no-store',
      })
      if (!response.ok) return false
      const text = await response.text()
      return !(
        text.includes('Whitelabel Error Page') ||
        text.includes('No static resource')
      )
    } catch {
      return false
    }
  }

  let lastLoggedPreviewUrl = ''

  const updatePreview = async () => {
    if (appRef.value?.previewUrl && appRef.value.previewUrl !== lastLoggedPreviewUrl) {
      console.log('[AppPreview] updatePreview, previewUrl:', appRef.value.previewUrl)
      lastLoggedPreviewUrl = appRef.value.previewUrl
    }
    previewWarning.value = ''

    // 如果还没有 previewUrl，先尝试刷新 app 数据
    if (!appRef.value?.previewUrl) {
      await refreshAppData()
    }

    const previewUrl = appRef.value?.previewUrl
    if (!previewUrl) {
      previewWarning.value = '预览地址暂不可用'
      previewStatus.value = 'failed'
      return
    }

    const nextUrl = `${previewUrl}${previewUrl.includes('?') ? '&' : '?'}t=${Date.now()}`
    previewStatus.value = 'checking'
    const resourceAvailable = await checkPreviewResource(nextUrl)
    if (resourceAvailable) {
      previewStatus.value = 'ready'
      iframeUrl.value = nextUrl
      return
    }

    if (iframeUrl.value) {
      previewStatus.value = 'ready'
      previewWarning.value = '预览资源检查失败，显示的是上一次的预览结果'
    } else {
      iframeUrl.value = ''
      previewStatus.value = 'idle'
    }
  }

  // ======== SSE 对话 ========
  const sseChat = useSSEChat({
    appId: options.appId,
    messages: options.messages,
    onPreviewUpdate: updatePreview,
    onSessionsUpdate: () => {
      refreshAppData()
      options.loadSessions()
    },
    onAppUpdate: (data) => {
      if (data.codeGenType && appRef.value) {
        appRef.value.codeGenType = data.codeGenType
      }
      options.onAppUpdate?.(data)
    },
  })

  return {
    // SSE 能力
    startSSE: sseChat.startSSE,
    stopSSE: sseChat.stopSSE,
    resumeSSE: sseChat.resumeSSE,
    generating: sseChat.generating,
    streamWarning: sseChat.streamWarning,
    // 预览状态
    iframeUrl,
    previewWarning,
    previewStatus,
    updatePreview,
    // 工具
    refreshAppData,
  }
}
