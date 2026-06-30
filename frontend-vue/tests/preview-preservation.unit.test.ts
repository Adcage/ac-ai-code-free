import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

test('TestChatPage: 发送对话与规划动作时不应主动清空已有预览 iframeUrl', () => {
  const source = readFileSync(new URL('../src/pages/admin/TestChatPage.vue', import.meta.url), 'utf8')

  const doChatSegment = source.match(/const doChatWithMessage[\s\S]*?const handleReloadCurrentSession/)
  assert.ok(doChatSegment, '应存在 doChatWithMessage 段落')
  assert.doesNotMatch(doChatSegment![0], /iframeUrl\.value\s*=\s*''/, '发送普通消息时不应清空已有预览')

  const planningSubmitSegment = source.match(/async function handlePlanningSubmit[\s\S]*?async function handlePlanConfirm/)
  assert.ok(planningSubmitSegment, '应存在 handlePlanningSubmit 段落')
  assert.doesNotMatch(planningSubmitSegment![0], /iframeUrl\.value\s*=\s*''/, '提交澄清答案时不应清空已有预览')

  const planConfirmSegment = source.match(/async function handlePlanConfirm[\s\S]*?function handlePlanningSkip/)
  assert.ok(planConfirmSegment, '应存在 handlePlanConfirm 段落')
  assert.doesNotMatch(planConfirmSegment![0], /iframeUrl\.value\s*=\s*''/, '确认计划时不应清空已有预览')
})
