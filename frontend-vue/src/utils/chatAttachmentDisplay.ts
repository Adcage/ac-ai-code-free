import type { AttachmentInfo } from '@/utils/chatStreamRequest'

export const ATTACHMENT_ONLY_MESSAGE = '[附件消息]'

export function parseChatHistoryAttachments(
  extra?: string | Record<string, unknown> | null,
): AttachmentInfo[] | undefined {
  if (!extra) return undefined
  try {
    const parsed = typeof extra === 'string' ? JSON.parse(extra) : extra
    const attachments = parsed?.attachments
    if (!Array.isArray(attachments) || attachments.length === 0) return undefined
    return attachments
  } catch {
    return undefined
  }
}

export function getDisplayMessageContent(
  content?: string | null,
  attachments?: AttachmentInfo[],
): string {
  if (content === ATTACHMENT_ONLY_MESSAGE && Array.isArray(attachments) && attachments.length > 0) {
    return ''
  }
  return content || ''
}

export function openAttachmentUrl(
  url?: string | null,
  opener: (url: string, target: string) => void = globalThis.window?.open?.bind(globalThis.window)!,
): void {
  if (!url || typeof opener !== 'function') return
  opener(url, '_blank')
}
