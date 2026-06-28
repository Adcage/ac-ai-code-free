export interface ChatAttachmentValidationResult {
  valid: boolean
  message: string
}

export const MAX_CHAT_ATTACHMENT_COUNT = 5
export const MAX_CHAT_ATTACHMENT_FILE_SIZE = 10 * 1024 * 1024
export const MAX_CHAT_ATTACHMENT_TOTAL_SIZE = 30 * 1024 * 1024

export function validateChatAttachmentFiles(
  files: Array<Pick<File, 'size' | 'name' | 'type'>>,
): ChatAttachmentValidationResult {
  if (!files || files.length === 0) {
    return { valid: true, message: '' }
  }
  if (files.length > MAX_CHAT_ATTACHMENT_COUNT) {
    return { valid: false, message: `最多上传 ${MAX_CHAT_ATTACHMENT_COUNT} 个文件` }
  }

  let totalSize = 0
  for (const file of files) {
    const size = Number(file?.size || 0)
    if (size > MAX_CHAT_ATTACHMENT_FILE_SIZE) {
      return { valid: false, message: '单个文件不能超过 10MB' }
    }
    totalSize += size
  }

  if (totalSize > MAX_CHAT_ATTACHMENT_TOTAL_SIZE) {
    return { valid: false, message: '文件总大小不能超过 30MB' }
  }

  return { valid: true, message: '' }
}
