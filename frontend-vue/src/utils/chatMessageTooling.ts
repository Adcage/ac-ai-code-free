import type { PlanningQuestionSet, ToolCallRecord, ToolEvent } from '../types/chat'

type ToolEventLike = {
  type?: string
  text?: string
}

type ToolSummaryInput = {
  status?: string
  toolStatus?: string
  toolCalls?: ToolCallRecord[]
}

const TOOL_REQUEST_TEXT: Record<string, string> = {
  Read: '正在查看文件',
  Write: '正在写入文件',
  Edit: '正在修改文件',
  Insert: '正在插入文件',
  Glob: '正在搜索文件',
  Grep: '正在搜索代码',
  Bash: '正在执行命令',
  LoadSkill: '正在加载设计方案',
  write_file: '正在写入文件',
  writeFile: '正在写入文件',
  read_file: '正在查看文件',
  readFile: '正在查看文件',
  modify_file: '正在修改文件',
  modifyFile: '正在修改文件',
  delete_file: '正在删除文件',
  deleteFile: '正在删除文件',
  read_dir: '正在查看目录结构',
  readDir: '正在查看目录结构',
  read_asset: '正在读取资源文件',
  run_command: '正在执行命令',
}

/** Agent 名称中文映射 */
const AGENT_DISPLAY_NAMES: Record<string, string> = {
  implementor: '实现',
  planner: '规划',
  validator: '校验',
  reviewer: '审查',
  architect: '架构',
}

const AGENT_BADGE_TEXT: Record<string, string> = {
  implementor: '执',
  planner: '规',
  validator: '校',
  reviewer: '审',
  architect: '构',
}

/** 获取 Agent 中文显示名 */
export function getAgentDisplayName(agentName: string): string {
  return AGENT_DISPLAY_NAMES[agentName] || agentName
}

export function getAgentBadgeText(agentName: string): string {
  return AGENT_BADGE_TEXT[agentName] || getAgentDisplayName(agentName).slice(0, 1)
}

export function resolveMessageAgentName(toolCalls?: ToolCallRecord[], agentName?: string): string {
  if (agentName?.trim()) {
    return agentName.trim()
  }
  const resolved = [...(toolCalls || [])].reverse().find((item) => item.agentName?.trim())?.agentName
  return resolved?.trim() || ''
}

export function buildMessageAgentSummary(toolCalls?: ToolCallRecord[], agentName?: string): string {
  const resolvedAgentName = resolveMessageAgentName(toolCalls, agentName)
  if (!resolvedAgentName) return ''
  return `${getAgentDisplayName(resolvedAgentName)}智能体`
}

export function normalizeToolEvents(events?: ToolEventLike[]): ToolEvent[] {
  if (!events || events.length === 0) return []
  return events
    .filter((item) => {
      return (
        (item.type === 'request' || item.type === 'executed' || item.type === 'status') &&
        typeof item.text === 'string' &&
        item.text.trim().length > 0
      )
    })
    .map((item) => ({
      type: item.type as ToolEvent['type'],
      text: item.text!.trim(),
    }))
}

export function parseToolCallsFromHistory(extra?: string | null, fallbackEvents?: ToolEventLike[]): ToolCallRecord[] {
  const structured = parseStructuredToolCalls(extra)
  if (structured.length > 0) {
    return structured
  }
  return normalizeToolEvents(fallbackEvents).map((eventItem, index) => ({
    type: eventItem.type,
    id: `legacy-${index}`,
    name: '历史记录',
    description: eventItem.text,
    arguments: '',
    status: eventItem.type === 'request' ? 'running' : eventItem.type === 'executed' ? 'completed' : 'running',
    timestamp: index,
  }))
}

export function parsePlanningFromExtra(toolCalls: ToolCallRecord[]): PlanningQuestionSet | undefined {
  const askUserEntry = toolCalls.find((tc) => tc.name === 'ask_user' && tc.type === 'request')
  if (!askUserEntry || !askUserEntry.arguments) return undefined
  try {
    const args = JSON.parse(askUserEntry.arguments)
    if (args.questions && Array.isArray(args.questions) && args.questions.length > 0) {
      return {
        questionSetId: args.questionSetId || args.questions[0]?.id || '',
        stage: args.stage,
        protocolVersion: args.protocolVersion,
        questions: args.questions,
      }
    }
  } catch {
    /* silent */
  }
  return undefined
}

export function buildMessageToolSummary(input: ToolSummaryInput): string {
  const toolCalls = input.toolCalls || []
  const runningCall = [...toolCalls].reverse().find((item) => item.status === 'running')

  if (input.status === 'running') {
    return input.toolStatus || runningCall?.description || 'AI 正在处理中'
  }

  if (input.status === 'failed') {
    return input.toolStatus || '生成失败'
  }

  if (toolCalls.length > 0) {
    return `已完成 ${toolCalls.length} 次工具调用`
  }

  if (input.status === 'success') {
    return '已完成'
  }

  return input.toolStatus || ''
}

export function resolveToolLogExpanded(expandedState: boolean | undefined, status?: string): boolean {
  if (expandedState !== undefined) {
    return expandedState
  }
  return status === 'running'
}

export function formatToolCallDescription(
  toolName?: string,
  argumentsText?: string,
  stage: 'request' | 'executed' = 'request',
  fallbackText?: string,
): string {
  if (fallbackText?.trim()) {
    return fallbackText.trim()
  }

  const path = parsePathFromArguments(argumentsText)
  const basename = path ? path.split('/').pop() || path : ''

  let desc = ''

  if (basename) {
    if (toolName === 'Read' || toolName === 'read_file' || toolName === 'readFile') desc = `正在查看 ${basename}`
    else if (toolName === 'Write' || toolName === 'write_file' || toolName === 'writeFile') desc = `正在写入 ${basename}`
    else if (toolName === 'Edit' || toolName === 'modify_file' || toolName === 'modifyFile') desc = `正在修改 ${basename}`
    else if (toolName === 'Insert' || toolName === 'insert') desc = `正在插入 ${basename}`
    else if (toolName === 'delete_file' || toolName === 'deleteFile') desc = `正在删除 ${basename}`
  }

  if (!desc) {
    if (stage === 'executed' && toolName) {
      desc = TOOL_REQUEST_TEXT[toolName] || `已执行 ${toolName}`
    } else {
      desc = TOOL_REQUEST_TEXT[toolName || ''] || `正在执行 ${toolName || '工具'}`
    }
  }

  return desc
}

function parseStructuredToolCalls(extra?: string | null): ToolCallRecord[] {
  if (!extra) return []

  try {
    const parsed = JSON.parse(extra)
    const rawToolCalls = Array.isArray(parsed?.toolCalls) ? parsed.toolCalls : []
    if (rawToolCalls.length === 0) return []

    const records: ToolCallRecord[] = []
    const recordIndexById = new Map<string, number>()

    rawToolCalls.forEach((item: Record<string, unknown>, index: number) => {
      const type = normalizeToolCallType(item.type)
      if (!type) return

      const id = typeof item.id === 'string' && item.id.trim() ? item.id.trim() : `history-${index}`
      const name = typeof item.name === 'string' ? item.name : ''
      const argumentsText = typeof item.arguments === 'string' ? item.arguments : ''
      const result = typeof item.result === 'string' ? item.result : ''
      const agentName = typeof item.agentName === 'string' ? item.agentName : ''

      if (type === 'request' || !recordIndexById.has(id)) {
        const nextRecord: ToolCallRecord = {
          type,
          id,
          name,
          description: formatToolCallDescription(name, argumentsText, 'request', undefined),
          arguments: argumentsText,
          result,
          status: type === 'executed' ? 'completed' : 'running',
          timestamp: index,
          agentName,
        }
        records.push(nextRecord)
        recordIndexById.set(id, records.length - 1)
        return
      }

      const existingIndex = recordIndexById.get(id)
      if (existingIndex === undefined) return

      records[existingIndex] = {
        ...records[existingIndex],
        type,
        name: name || records[existingIndex].name,
        arguments: argumentsText || records[existingIndex].arguments,
        result: result || records[existingIndex].result,
        status: type === 'executed' ? 'completed' : records[existingIndex].status,
      }
    })

    return records
  } catch {
    return []
  }
}

function normalizeToolCallType(type: unknown): ToolCallRecord['type'] | '' {
  if (type === 'request' || type === 'executed' || type === 'status') {
    return type
  }
  return ''
}

function parsePathFromArguments(argumentsText?: string) {
  if (!argumentsText) return ''

  try {
    const argsObj = JSON.parse(argumentsText)
    return (
      argsObj.path ||
      argsObj.relative_path ||
      argsObj.relativeFilePath ||
      argsObj.relative_dir_path ||
      argsObj.relativeDirPath ||
      ''
    )
  } catch {
    return ''
  }
}
