import test from 'node:test'
import assert from 'node:assert/strict'
import { createJiti } from 'jiti'

const jiti = createJiti(import.meta.url, {
  interopDefault: true,
  moduleCache: false,
})

const { buildChatStreamRequestBody } = jiti('../src/utils/chatStreamRequest.ts')

test('buildChatStreamRequestBody: 雪花 ID 必须保持字符串，避免 Number 精度丢失', () => {
  const requestBody = buildChatStreamRequestBody({
    appId: '1978456123456789012',
    sessionId: '1978456123456789456',
    message: '请生成登录页',
    displayMessage: '请生成登录页',
  })

  assert.deepEqual(requestBody, {
    appId: '1978456123456789012',
    sessionId: '1978456123456789456',
    message: '请生成登录页',
    displayMessage: '请生成登录页',
  })
  assert.equal(typeof requestBody.appId, 'string')
  assert.equal(typeof requestBody.sessionId, 'string')
})

test('buildChatStreamRequestBody: 缺少 sessionId 时不应补 Number 0', () => {
  const requestBody = buildChatStreamRequestBody({
    appId: '1978456123456789012',
    message: '继续生成',
  })

  assert.deepEqual(requestBody, {
    appId: '1978456123456789012',
    message: '继续生成',
    displayMessage: '继续生成',
  })
  assert.equal('sessionId' in requestBody, false)
})

test('buildChatStreamRequestBody: 携带附件时应在请求体中包含 attachments', () => {
  const attachments = [
    {
      id: 'att-1',
      fileName: 'screenshot.png',
      fileSize: 204800,
      mimeType: 'image/png',
      storageType: 'local',
      storagePath: 'chat_attachments/2026/06/27/att-1.png',
      url: 'http://localhost:8700/api/file/chat-attachment/...',
    },
    {
      id: 'att-2',
      fileName: 'utils.py',
      fileSize: 5120,
      mimeType: 'text/x-python',
      storageType: 'local',
      storagePath: 'chat_attachments/2026/06/27/att-2.py',
      url: 'http://localhost:8700/api/file/chat-attachment/...',
    },
  ]

  const requestBody = buildChatStreamRequestBody({
    appId: '123',
    sessionId: '456',
    message: '重写这个代码',
    displayMessage: '重写这个代码',
    attachments,
  })

  assert.equal(Array.isArray(requestBody.attachments), true)
  assert.equal(requestBody.attachments.length, 2)
  assert.equal(requestBody.attachments[0].fileName, 'screenshot.png')
  assert.equal(requestBody.attachments[0].mimeType, 'image/png')
  assert.equal(requestBody.attachments[1].fileName, 'utils.py')
  assert.equal(requestBody.attachments[1].mimeType, 'text/x-python')
})

test('buildChatStreamRequestBody: 空附件数组不应出现在请求体中', () => {
  const requestBody = buildChatStreamRequestBody({
    appId: '123',
    message: 'test',
    attachments: [],
  })

  assert.equal('attachments' in requestBody, false)
})

test('buildChatStreamRequestBody: 附件携带完整的 AttachmentInfo 字段', () => {
  const attachments = [
    {
      id: 'att-1',
      fileName: 'screenshot.png',
      fileSize: 204800,
      mimeType: 'image/png',
      storageType: 'local',
      storagePath: 'chat_attachments/...',
      url: 'http://localhost:8700/api/file/chat-attachment/...',
    },
  ]

  const requestBody = buildChatStreamRequestBody({
    appId: '123',
    message: 'test',
    attachments,
  })

  const att = requestBody.attachments[0]
  assert.equal(att.id, 'att-1')
  assert.equal(att.fileName, 'screenshot.png')
  assert.equal(att.fileSize, 204800)
  assert.equal(att.mimeType, 'image/png')
  assert.equal(att.storageType, 'local')
  assert.equal(att.storagePath, 'chat_attachments/...')
  assert.equal(att.url, 'http://localhost:8700/api/file/chat-attachment/...')
})
