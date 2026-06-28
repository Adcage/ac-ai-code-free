import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

import {
  buildMessageToolSummary,
  parseToolCallsFromHistory,
} from '../src/utils/chatMessageTooling.ts'

test('parseToolCallsFromHistory: 优先从 extra.toolCalls 恢复结构化工具调用并按 id 合并状态', () => {
  const extra = JSON.stringify({
    toolCalls: [
      {
        type: 'request',
        id: 'tool-1',
        name: 'Write',
        arguments: '{"path":"src/App.vue"}',
      },
      {
        type: 'executed',
        id: 'tool-1',
        name: 'Write',
        arguments: '{"path":"src/App.vue"}',
        result: 'ok',
      },
    ],
  })

  const result = parseToolCallsFromHistory(extra)

  assert.equal(result.length, 1)
  assert.equal(result[0].id, 'tool-1')
  assert.equal(result[0].name, 'Write')
  assert.equal(result[0].status, 'completed')
  assert.match(result[0].description, /App\.vue/)
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
