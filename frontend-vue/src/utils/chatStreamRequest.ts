export interface AttachmentInfo {
  id: string
  fileName: string
  fileSize: number
  mimeType: string
  storageType: string
  storagePath: string
  url: string
}

export interface ChatStreamRequestInput {
  appId: string | number
  sessionId?: string | number | null
  message: string
  displayMessage?: string
  attachments?: AttachmentInfo[]
}

export interface ChatStreamRequestBody {
  appId: string
  sessionId?: string
  message: string
  displayMessage: string
  attachments?: AttachmentInfo[]
}

/**
 * 构造聊天流请求体。
 *
 * 关键约束：Long / Snowflake ID 必须保持字符串传输，
 * 禁止在前端转成 Number，避免精度丢失导致后端查不到会话或应用。
 */
export function buildChatStreamRequestBody(input: ChatStreamRequestInput): ChatStreamRequestBody {
  const body: ChatStreamRequestBody = {
    appId: String(input.appId),
    message: input.message,
    displayMessage: input.displayMessage || input.message,
  }
  if (input.sessionId !== undefined && input.sessionId !== null && input.sessionId !== '') {
    body.sessionId = String(input.sessionId)
  }
  if (input.attachments && input.attachments.length > 0) {
    body.attachments = input.attachments
  }
  return body
}
