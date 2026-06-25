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
