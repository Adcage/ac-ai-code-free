<template>
  <div class="chat-message-list" ref="listRef">
    <div v-if="hasMore" class="load-more-bar">
      <a-button type="link" size="small" @click="$emit('loadEarlier')">加载更早的消息</a-button>
    </div>
    <div
      v-for="(msg, index) in messages"
      :key="index"
      :class="['message-item', msg.role === 'user' ? 'user-msg' : 'ai-msg']"
    >
      <a-avatar :src="msg.role === 'user' ? userAvatar : '/ai-avatar.png'" />
      <div class="message-body">
        <template v-if="msg.role === 'ai' && getPlanningData(index)">
          <PlanningForm
            v-if="getPlanningData(index)!.planningType === 'clarification' && (getPlanningData(index) as Extract<PlanningData, { planningType: 'clarification' }>).questions"
            :questions="(getPlanningData(index) as Extract<PlanningData, { planningType: 'clarification' }>).questions"
            :readonly-answers="getPlanningAnswers(index)"
            @submit="(answers: Record<string, string>) => $emit('planningSubmit', answers)"
            @skip="$emit('planningSkip', index)"
          />
          <PlanConfirmationCard
            v-else-if="getPlanningData(index)!.planningType === 'plan_confirmation' && (getPlanningData(index) as Extract<PlanningData, { planningType: 'plan_confirmation' }>).outline"
            :outline="(getPlanningData(index) as Extract<PlanningData, { planningType: 'plan_confirmation' }>).outline"
            @confirm="$emit('planConfirm', index)"
            @cancel="$emit('planningSkip', index)"
          />
        </template>
        <template v-else-if="msg.role === 'ai'">
          <div class="message-content">
            <template v-for="parsed in [parseAiMessage(msg.content, msg.toolEvents || [])]" :key="`parsed-${index}`">
              <div
                v-if="parsed.aiText"
                class="message-text"
                v-html="renderMarkdown(parsed.aiText)"
                @click="handleMessageTextClick"
              ></div>
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
                      {{
                        eventItem.type === 'request'
                          ? '调用中'
                          : eventItem.type === 'executed'
                            ? '已完成'
                            : '进行中'
                      }}
                    </span>
                    <span class="tool-call-text">{{ eventItem.text }}</span>
                  </div>
                </div>
              </details>
            </template>
          </div>
        </template>
        <template v-else>
          <div v-if="getImageAttachments(msg.attachments).length > 0" class="user-message-media attachments-preview attachments-preview-images">
            <div class="user-message-media-stack">
              <button
                v-for="att in getImageAttachments(msg.attachments)"
                :key="att.id"
                type="button"
                class="attachment-image-card"
                @click="openImagePreview(att.url)"
              >
                <img :src="att.url" :alt="att.fileName" class="attachment-image-thumb" />
              </button>
            </div>
          </div>
          <div v-if="getFileAttachments(msg.attachments).length > 0" class="attachments-preview attachments-preview-files">
            <div v-for="att in getFileAttachments(msg.attachments)" :key="att.id" class="attachment-chip">
              <PaperClipOutlined />
              <span class="attachment-label">{{ att.fileName }}</span>
            </div>
          </div>
          <div
            v-if="hasDisplayMessageContent(msg.content, msg.attachments)"
            class="message-content user-message-bubble"
          >
            <div
              class="message-text"
              v-html="renderMarkdown(getDisplayMessageContent(msg.content, msg.attachments))"
            ></div>
          </div>
        </template>
      </div>
    </div>
    <div v-if="generating" class="generating-indicator"><LoadingOutlined /> AI 正在思考并生成代码...</div>

    <div v-if="streamWarning" class="stream-warning">
      <a-alert type="warning" show-icon :message="streamWarning" />
      <a-button type="link" size="small" @click="$emit('reloadSession')">重新加载当前会话</a-button>
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
          <a-button size="small" type="link" @click="$emit('clearSelectedElement')">清除</a-button>
        </template>
      </a-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { LoadingOutlined, PaperClipOutlined } from '@ant-design/icons-vue'
import MarkdownIt from 'markdown-it'
import PlanningForm from '@/components/PlanningForm.vue'
import PlanConfirmationCard from '@/components/PlanConfirmationCard.vue'
import { getDisplayMessageContent } from '@/utils/chatAttachmentDisplay'

export interface ToolEvent {
  type: 'request' | 'executed' | 'status'
  text: string
}

export interface ChatMessage {
  role: 'user' | 'ai'
  content: string
  status?: string
  toolEvents?: ToolEvent[]
  planning?: PlanningQuestionSet
  attachments?: AttachmentInfo[]
}

export interface AttachmentInfo {
  id: string
  fileName: string
  fileSize: number
  mimeType: string
  storageType: string
  storagePath: string
  url: string
}

export interface ElementInfo {
  tagName: string
  pagePath?: string
  selector?: string
  textContent?: string
  [key: string]: unknown
}

type PlanningOption = {
  id?: string
  value?: string
  label: string
  description?: string
  recommended?: boolean
}

type PlanningQuestion = {
  id: string
  prompt?: string
  question: string
  inputType: 'single_select' | 'multi_select'
  required: boolean
  options?: PlanningOption[]
  reason?: string
  placeholder?: string
}

type PlanningQuestionSet = {
  questionSetId: string
  stage?: string
  protocolVersion?: number
  questions: PlanningQuestion[]
}

type PlanningData =
  | {
      planningType: 'clarification'
      questionSetId?: string
      questions: PlanningQuestion[]
      // 兼容旧字段
      question?: string
      inputType?: string
      options?: PlanningOption[]
      required?: boolean
    }
  | { planningType: 'plan_confirmation'; outline: PlanOutline; title?: string }

type PlanOutline = {
  title: string
  summary: string
  steps: string[]
  risks: string[]
  assumptions: string[]
}

const PLANNING_TAG_RE = /<planning\s+type="(\w+)"\s*>([\s\S]*?)<\/planning>/

const props = withDefaults(
  defineProps<{
    messages: ChatMessage[]
    generating?: boolean
    streamWarning?: string
    userAvatar?: string
    selectedElement?: ElementInfo | null
    hasMore?: boolean
  }>(),
  {
    generating: false,
    streamWarning: '',
    userAvatar: '',
    selectedElement: null,
    hasMore: false,
  },
)

defineEmits<{
  planningSubmit: [answers: Record<string, string>]
  planningSkip: [index: number]
  planConfirm: [index: number]
  reloadSession: []
  clearSelectedElement: []
  loadEarlier: []
}>()

const listRef = ref<HTMLElement>()

function getPlanningData(index: number): PlanningData | null {
  const msg = props.messages[index]
  if (!msg || msg.role !== 'ai') return null

  // 优先使用结构化 planning 字段（Phase 3）
  if (msg.planning && msg.planning.questions && msg.planning.questions.length > 0) {
    return {
      planningType: 'clarification',
      questionSetId: msg.planning.questionSetId,
      questions: msg.planning.questions.map((q) => ({
        id: q.id,
        question: q.question,
        inputType: q.inputType,
        required: q.required,
        options: q.options || [],
        reason: q.reason,
        placeholder: q.placeholder,
      })),
    }
  }

  // 回退到旧的 <planning> 标签解析（历史消息兼容）
  const match = msg.content.match(PLANNING_TAG_RE)
  if (!match) return null
  try {
    const data = JSON.parse(match[2])
    return { planningType: match[1] as PlanningData['planningType'], ...data }
  } catch {
    return null
  }
}

function getPlanningAnswers(index: number): Record<string, string> | null {
  const data = getPlanningData(index)
  if (!data || data.planningType !== 'clarification') return null
  const nextUserMsg = props.messages.slice(index + 1).find((m) => m.role === 'user')
  if (!nextUserMsg) return null
  const answers: Record<string, string> = {}
  for (const q of data.questions) {
    // 优先按 question.id 精确匹配；保留旧 question 文本匹配作为兜底
    const direct = nextUserMsg.content.match(new RegExp(`\\[\\s*${q.id}\\s*[：:]\\s*([^\\n]+)`, 'i'))
    if (direct) {
      answers[q.id] = direct[1].trim()
      continue
    }
    const escapedQ = q.question.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const answerRe = new RegExp(`${escapedQ}\\s*[：:]\\s*答[：:]\\s*(.+?)(?:\\n|$)`, 'i')
    const qaMatch = nextUserMsg.content.match(answerRe)
    if (qaMatch) {
      answers[q.id] = qaMatch[1].trim()
    }
  }
  return Object.keys(answers).length > 0 ? answers : null
}

function parseAiMessage(
  content: string,
  presetToolEvents: ToolEvent[] = [],
): { aiText: string; toolEvents: ToolEvent[] } {
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
    if (trimmedLine === 'waiting_for_user' || trimmedLine.startsWith('Agent loop completed:')) {
      return
    }
    if (trimmedLine.startsWith('[状态]')) {
      toolEvents.push({ type: 'status', text: trimmedLine.replace('[状态]', '').trim() || '处理中' })
      return
    }
    if (trimmedLine.startsWith('[工具调用]')) {
      toolEvents.push({ type: 'request', text: trimmedLine.replace('[工具调用]', '').trim() || '执行工具调用' })
      return
    }
    if (trimmedLine.startsWith('[工具完成]')) {
      toolEvents.push({ type: 'executed', text: trimmedLine.replace('[工具完成]', '').trim() || '工具执行成功' })
      return
    }
    if (trimmedLine.startsWith('准备写入文件')) {
      toolEvents.push({ type: 'request', text: trimmedLine })
      return
    }
    if (trimmedLine.startsWith('已写入文件')) {
      toolEvents.push({ type: 'executed', text: trimmedLine })
      return
    }
    aiTextLines.push(line)
  })

  return { aiText: aiTextLines.join('\n').trim(), toolEvents }
}

function stripToolEventLines(content: string) {
  return content
    .replace(/\n?waiting_for_user\n?/g, '')
    .replace(/\n?Agent loop completed:.*?\n?/g, '')
    .split('\n')
    .filter((line) => {
      const trimmedLine = line.trim()
      return !(
        trimmedLine.startsWith('[工具调用]') ||
        trimmedLine.startsWith('[工具完成]') ||
        trimmedLine.startsWith('[状态]') ||
        trimmedLine.startsWith('准备写入文件') ||
        trimmedLine.startsWith('已写入文件')
      )
    })
    .join('\n')
}

function getImageAttachments(attachments?: AttachmentInfo[]) {
  return (attachments || []).filter((att) => att.mimeType.startsWith('image/'))
}

function getFileAttachments(attachments?: AttachmentInfo[]) {
  return (attachments || []).filter((att) => !att.mimeType.startsWith('image/'))
}

function hasDisplayMessageContent(content: string, attachments?: AttachmentInfo[]) {
  return getDisplayMessageContent(content, attachments).trim().length > 0
}

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

/**
 * Markdown 文本预处理：修复模型输出的常见格式问题
 * - ATX 标题缺少空格：##标题 → ## 标题
 * - 列表符号缺少空格：-项目 → - 项目
 */
const preprocessMarkdown = (text: string): string => {
  return (
    text
      // 修复 ATX 标题：行首 1-6 个 # 后紧跟非空格字符，在 # 和内容之间插入空格
      .replace(/^(#{1,6})([^#\s])/gm, '$1 $2')
      // 修复无序列表：行首 - 或 * 后紧跟非空格字符
      .replace(/^(\s*[-*])(\S)/gm, '$1 $2')
  )
}

const renderMarkdown = (text: string) => {
  return md.render(preprocessMarkdown(text))
}

/** 通过自定义事件打开图片预览（绕过 composable 模块隔离问题） */
function openImagePreview(url: string) {
  window.dispatchEvent(new CustomEvent('image-preview-open', { detail: url }))
}

/** 事件委托：点击 v-html 渲染的 <img> 时打开图片预览 */
function handleMessageTextClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target.tagName === 'IMG') {
    const src = (target as HTMLImageElement).src
    if (src) {
      e.preventDefault()
      openImagePreview(src)
    }
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight
    }
  })
}

// 消息变化时自动滚动
watch(
  () => props.messages.length,
  () => scrollToBottom(),
)

defineExpose({ scrollToBottom, listRef })
</script>

<style scoped>
.chat-message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--color-background);
}

.message-item {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.message-item.user-msg {
  flex-direction: row-reverse;
}

.attachments-preview {
  margin-bottom: 10px;
}

.attachments-preview-images {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.attachments-preview-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.attachment-image-card {
  display: block;
  width: clamp(64px, 14vw, 112px);
  overflow: hidden;
  padding: 0;
  border: none;
  border-radius: 18px;
  background: transparent;
  box-shadow: none;
  cursor: pointer;
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.attachment-image-card:hover {
  transform: translateY(-1px);
}

.attachment-image-thumb {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border-radius: 18px;
  box-shadow:
    0 10px 26px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.08);
}

.attachment-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  cursor: default;
}

.attachment-label {
  font-size: 12px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text-secondary);
}

.message-item.user-msg .message-body {
  align-items: flex-end;
}

.message-item.user-msg .attachments-preview-images {
  justify-content: flex-end;
}

.user-message-media {
  width: 100%;
}

.user-message-media-stack {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

.message-item.user-msg .attachment-image-card {
  background: transparent;
}

.user-message-bubble {
  align-self: flex-end;
  max-width: min(420px, 100%);
}

.message-body {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-content {
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.user-msg .message-content {
  background: var(--color-secondary);
  color: var(--color-text-on-cta);
  border-bottom-right-radius: 2px;
}

.ai-msg .message-content {
  background: var(--color-surface-hover);
  color: var(--color-text);
  border-left: 3px solid var(--color-cta);
  border-bottom-left-radius: 2px;
}

.message-text :deep(code) {
  background: rgba(28, 24, 21, 0.06);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 13px;
}

.message-text :deep(pre) {
  background: rgba(28, 24, 21, 0.04);
  padding: 8px 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 13px;
}

.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4) {
  margin: 12px 0 6px;
  font-weight: 600;
  line-height: 1.4;
  font-family: var(--font-heading);
}

.message-text :deep(h1) { font-size: 18px; }
.message-text :deep(h2) { font-size: 16px; }
.message-text :deep(h3) { font-size: 15px; }
.message-text :deep(h4) { font-size: 14px; }

.message-text :deep(ul),
.message-text :deep(ol) {
  padding-left: 20px;
  margin: 6px 0;
}

.message-text :deep(li) {
  margin: 2px 0;
}

.message-text :deep(p) {
  margin: 4px 0;
}

.message-text :deep(blockquote) {
  border-left: 3px solid var(--color-cta-light);
  padding-left: 10px;
  margin: 8px 0;
  color: var(--color-text-secondary);
}

.message-text :deep(a) {
  color: var(--color-cta);
  text-decoration: none;
}

.message-text :deep(a:hover) {
  text-decoration: underline;
  color: var(--color-cta-hover);
}

.message-text :deep(img) {
  max-width: 100%;
  border-radius: 16px;
  cursor: pointer;
  box-shadow:
    0 10px 24px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.08);
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.message-text :deep(img:hover) {
  opacity: 0.85;
  transform: translateY(-1px);
}

.user-msg .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.95);
}

.tool-call-card {
  margin-top: 8px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
  background: var(--color-surface);
}

.tool-call-summary {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  background: var(--color-surface-hover);
}

.tool-call-title {
  font-weight: 500;
  color: var(--color-text-secondary);
}

.tool-call-hint {
  color: var(--color-text-muted);
}

.tool-call-list {
  padding: 8px 12px;
}

.tool-call-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
}

.tool-call-tag {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.tool-call-tag.request {
  background: #e6f7ff;
  color: #1890ff;
}

.tool-call-tag.executed {
  background: #f6ffed;
  color: #52c41a;
}

.tool-call-tag.status {
  background: #fff7e6;
  color: #fa8c16;
}

.tool-call-text {
  color: var(--color-text-secondary);
}

.generating-indicator {
  text-align: center;
  padding: 16px;
  color: var(--color-text-tertiary);
  font-size: 13px;
}

.stream-warning {
  padding: 0 16px 8px;
}

.selected-element-panel {
  padding: 8px 16px;
}

.selected-element-content {
  font-size: 12px;
  line-height: 1.8;
}
</style>
