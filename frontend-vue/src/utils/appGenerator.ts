export const formatCodeGenType = (codeGenType?: string) => {
  if (codeGenType === 'single_file') return '单文件模式'
  if (codeGenType === 'multi-file') return '多文件模式'
  if (codeGenType === 'vue_project') return 'Vue 项目模式'
  return codeGenType || '未知模式'
}

export const formatCoverTaskStatus = (status?: string, retryCount?: number) => {
  if (status === 'PENDING') return '封面任务待执行'
  if (status === 'RUNNING') return `封面生成中（第 ${retryCount || 1} 次）`
  if (status === 'SUCCESS') return '封面已更新'
  if (status === 'SKIPPED') return '已保留原封面'
  if (status === 'FAILED') return `封面生成失败（重试 ${retryCount || 0} 次）`
  return '封面状态未知'
}

export const coverTaskStatusColor = (status?: string) => {
  if (status === 'PENDING') return 'gold'
  if (status === 'RUNNING') return 'processing'
  if (status === 'SUCCESS') return 'success'
  if (status === 'SKIPPED') return 'default'
  if (status === 'FAILED') return 'error'
  return 'default'
}

export const looksLikeRiskRejection = (content: string) => {
  const lowerContent = content.toLowerCase()
  return (
    lowerContent.includes('the request was rejected') ||
    lowerContent.includes('considered high risk') ||
    lowerContent.includes('内容安全') ||
    lowerContent.includes('内容违规')
  )
}

export const looksLikeGenerationFailure = (content: string) => {
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

export const hasFileWriteSignal = (messageItem: {
  toolEvents?: { type: string; text: string }[]
  toolCalls?: { name?: string; description?: string; status?: string }[]
  content?: string
}) => {
  if (messageItem.toolCalls?.some((toolCall) => {
    return (
      toolCall.status === 'completed' &&
      (
        toolCall.name === 'Write' ||
        toolCall.name === 'write_file' ||
        toolCall.name === 'writeFile' ||
        toolCall.description?.includes('写入')
      )
    )
  })) {
    return true
  }
  if (messageItem.toolEvents?.some((eventItem) => eventItem.type === 'executed' && eventItem.text.includes('写入文件'))) {
    return true
  }
  return (messageItem.content ?? '').includes('[工具完成]') || (messageItem.content ?? '').includes('已写入文件')
}

export const hasPreviewCandidate = (messages: {
  role: string
  status?: string
  content?: string
  toolEvents?: { type: string; text: string }[]
  toolCalls?: { name?: string; description?: string; status?: string }[]
}[]) => {
  const latestAiMessage = [...messages].reverse().find((item) => item.role === 'ai')
  if (!latestAiMessage || latestAiMessage.status === 'failed' || looksLikeGenerationFailure(latestAiMessage.content ?? '')) {
    return false
  }
  return latestAiMessage.status === 'success' || hasFileWriteSignal(latestAiMessage)
}

export const hasLatestGenerationFailure = (messages: { role: string; status?: string; content?: string }[]) => {
  const latestAiMessage = [...messages].reverse().find((item) => item.role === 'ai')
  return (
    !!latestAiMessage && (latestAiMessage.status === 'failed' || looksLikeGenerationFailure(latestAiMessage.content ?? ''))
  )
}

export const extractLatestFailureReason = (messages: { role: string; content?: string }[]) => {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const item = messages[i]
    if (item.role !== 'ai' || !item.content) continue
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
    if (failureLine) return failureLine
  }
  return ''
}

export const isTimeoutFailureReason = (reason: string) => {
  const lowerReason = reason.toLowerCase()
  return lowerReason.includes('timeout') || lowerReason.includes('timed out') || lowerReason.includes('read timed out')
}

export const buildSelectedElementPrompt = (userInput: string, selectedElement: { textContent?: string; selector?: string; pagePath?: string; tagName: string } | null) => {
  if (!selectedElement) return userInput
  const target = selectedElement
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
