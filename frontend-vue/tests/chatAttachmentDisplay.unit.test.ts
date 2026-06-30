import test from 'node:test'
import assert from 'node:assert/strict'
import {
  getDisplayMessageContent,
  openAttachmentUrl,
  parseChatHistoryAttachments,
} from '../src/utils/chatAttachmentDisplay'

const attachment = {
  id: 'att-1',
  fileName: 'design.jpg',
  fileSize: 1024,
  mimeType: 'image/jpeg',
  storageType: 'local',
  storagePath: 'chat_attachments/2026/06/27/design.jpg',
  url: 'http://localhost:8700/api/storage/chat_attachments/2026/06/27/design.jpg',
}

test('parseChatHistoryAttachments: 从历史 extra 中还原附件列表', () => {
  const result = parseChatHistoryAttachments(JSON.stringify({ attachments: [attachment] }))

  assert.equal(result!.length, 1)
  assert.equal(result![0].id, 'att-1')
  assert.equal(result![0].mimeType, 'image/jpeg')
})

test('getDisplayMessageContent: 有附件时隐藏纯附件兜底文本', () => {
  const result = getDisplayMessageContent('[附件消息]', [attachment])

  assert.equal(result, '')
})

test('getDisplayMessageContent: 普通文本照常展示', () => {
  const result = getDisplayMessageContent('请参考图片做页面', [attachment])

  assert.equal(result, '请参考图片做页面')
})

test('openAttachmentUrl: 使用传入 opener 在新标签页打开附件', () => {
  const calls: Array<{ url: string; target: string }> = []

  openAttachmentUrl(attachment.url, (url, target) => calls.push({ url, target }))

  assert.deepEqual(calls, [{ url: attachment.url, target: '_blank' }])
})
