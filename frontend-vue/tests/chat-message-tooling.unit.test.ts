import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

import {
  buildMessageAgentSummary,
  buildMessageToolSummary,
  formatToolCallDescription,
  getAgentBadgeText,
  getToolDisplayName,
  parseToolCallsFromHistory,
  resolveToolLogExpanded,
} from '../src/utils/chatMessageTooling.ts'

test('parseToolCallsFromHistory: 优先从 extra.toolCalls 恢复结构化工具调用并按 id 合并状态', () => {
  const extra = JSON.stringify({
    toolCalls: [
      {
        type: 'request',
        id: 'tool-1',
        name: 'Write',
        arguments: '{"path":"src/App.vue"}',
        agentName: 'implementor',
      },
      {
        type: 'executed',
        id: 'tool-1',
        name: 'Write',
        arguments: '{"path":"src/App.vue"}',
        result: 'ok',
        agentName: 'implementor',
      },
    ],
  })

  const result = parseToolCallsFromHistory(extra)

  assert.equal(result.length, 1)
  assert.equal(result[0].id, 'tool-1')
  assert.equal(result[0].name, 'Write')
  assert.equal(result[0].status, 'completed')
  assert.match(result[0].description, /App\.vue/)
  assert.doesNotMatch(result[0].description, /\[实现\]/, '动作描述不应再重复拼接完整智能体标签')
  assert.equal(result[0].agentName, 'implementor')
})

test('parseToolCallsFromHistory: 没有结构化 toolCalls 时回退旧版 toolEvents', () => {
  const result = parseToolCallsFromHistory(undefined, [
    { type: 'request', text: '正在搜索文件' },
    { type: 'executed', text: '已写入文件 src/App.vue' },
  ])

  assert.equal(result.length, 2)
  assert.equal(result[0].status, 'running')
  assert.equal(result[0].description, '正在搜索文件')
  assert.equal(result[1].status, 'completed')
  assert.equal(result[1].description, '已写入文件 src/App.vue')
})

test('buildMessageToolSummary: 运行中优先显示当前状态，成功后汇总工具数量，失败时返回失败状态', () => {
  assert.equal(
    buildMessageToolSummary({
      status: 'running',
      toolStatus: '正在修改 Header.vue',
      toolCalls: [],
    }),
    '正在修改 Header.vue',
  )

  assert.equal(
    buildMessageToolSummary({
      status: 'success',
      toolStatus: '',
      toolCalls: [
        {
          id: 'tool-1',
          type: 'executed',
          name: 'Read',
          description: '正在查看 App.vue',
          arguments: '{}',
          status: 'completed',
          timestamp: 1,
        },
        {
          id: 'tool-2',
          type: 'executed',
          name: 'Write',
          description: '正在写入 App.vue',
          arguments: '{}',
          status: 'completed',
          timestamp: 2,
        },
      ],
    }),
    '已完成 2 次工具调用',
  )

  assert.equal(
    buildMessageToolSummary({
      status: 'failed',
      toolStatus: '',
      toolCalls: [],
    }),
    '生成失败',
  )
})

test('buildMessageAgentSummary/getAgentBadgeText: 顶部使用完整身份，明细使用单字徽标', () => {
  assert.equal(
    buildMessageAgentSummary(
      [
        {
          id: 'tool-1',
          type: 'request',
          name: 'Read',
          description: '正在查看 App.vue',
          arguments: '{}',
          status: 'running',
          timestamp: 1,
          agentName: 'implementor',
        },
      ],
      '',
    ),
    '实现智能体',
  )

  assert.equal(getAgentBadgeText('implementor'), '执')
  assert.equal(getAgentBadgeText('planner'), '规')
  assert.equal(getAgentBadgeText('conductor'), '总')
  assert.equal(buildMessageAgentSummary([], 'conductor'), '总控智能体')
})

test('delegate_to_agent: 应显示派遣目标而不是原始工具名', () => {
  const args = JSON.stringify({ agent_name: 'implementor', task: '实现登录页' })

  assert.equal(getToolDisplayName('delegate_to_agent', args), '派遣子智能体：实现智能体')
  assert.equal(
    formatToolCallDescription('delegate_to_agent', args, 'request'),
    '正在派遣实现智能体',
  )
})

test('resolveToolLogExpanded: 运行中默认展开，但用户显式收起后不应自动反弹', () => {
  assert.equal(resolveToolLogExpanded(undefined, 'running'), true)
  assert.equal(resolveToolLogExpanded(false, 'running'), false)
  assert.equal(resolveToolLogExpanded(true, 'running'), true)
  assert.equal(resolveToolLogExpanded(undefined, 'success'), false)
})

test('ChatMessageList: AI 消息应包含消息级状态头和工具记录容器', () => {
  const source = readFileSync(new URL('../src/components/ChatMessageList.vue', import.meta.url), 'utf8')

  assert.match(source, /message-tool-summary/, 'AI 消息上方应渲染状态头容器')
  assert.match(source, /message-tool-log/, 'AI 消息应提供消息级工具记录容器')
})

test('ChatMessageList: 工具详情应使用浮层定位而不是继续参与消息流布局', () => {
  const source = readFileSync(new URL('../src/components/ChatMessageList.vue', import.meta.url), 'utf8')

  assert.match(source, /position:\s*absolute/, '桌面端工具详情应脱离文档流，避免撑开消息')
  assert.match(source, /@media\s*\(max-width:\s*768px\)/, '移动端应提供浮层降级样式')
  assert.match(source, /document\.addEventListener\('click',\s*handleDocumentClick\)/, '应支持点击外部关闭浮层')
})

test('ChatMessageList: Markdown 中的 <br> 应恢复为安全换行，表格应有专门样式', () => {
  const source = readFileSync(new URL('../src/components/ChatMessageList.vue', import.meta.url), 'utf8')

  assert.match(
    source,
    /replace\(\/&lt;br\\s\*\\\/\?&gt;\/gi,\s*'<br\s*\/>'\)/,
    '应显式处理 markdown 渲染后被转义的 <br> 标签',
  )
  assert.match(source, /:deep\(table\)/, '消息中的 markdown 表格应提供专门样式')
  assert.match(source, /:deep\(th\)/, '表头单元格应提供样式')
  assert.match(source, /:deep\(td\)/, '表格单元格应提供样式')
})

test('ChatMessageList: 智能体标签应与工具名同排显示，避免单独占一行', () => {
  const source = readFileSync(new URL('../src/components/ChatMessageList.vue', import.meta.url), 'utf8')

  assert.match(source, /message-tool-log-heading/, '工具明细应提供标题行容器，把智能体标签与工具名放在同一行')
  assert.match(source, /message-tool-summary-agent/, '顶部摘要应提供智能体身份文案容器')
  assert.match(source, /message-tool-log-badge/, '明细中应使用弱化单字徽标，而不是完整智能体标签')
})

test('useSSEChat: tool_executed 和 status 事件也应回填当前智能体身份', () => {
  const source = readFileSync(new URL('../src/composables/useSSEChat.ts', import.meta.url), 'utf8')

  assert.match(source, /existing\.agentName\s*=\s*agentName\s*\|\|\s*existing\.agentName/, '已存在工具记录在 tool_executed 时也应补写 agentName')
  assert.match(source, /targetMessage\.agentName\s*=\s*agentName/, 'tool_executed 或 status 应把消息级 agentName 回填到当前消息')
  assert.match(source, /targetMessage\.currentAgent\s*=\s*agentName/, 'status 或 agent_start 事件应维护当前智能体身份')
})
