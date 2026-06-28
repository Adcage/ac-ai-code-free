import test from 'node:test'
import assert from 'node:assert/strict'
import { validateChatAttachmentFiles } from '../src/utils/chatAttachmentValidation'

const mb = 1024 * 1024
const file = (name: string, size: number, type = 'image/jpeg') => ({ name, size, type })

test('拒绝超过 10MB 的单个聊天附件', () => {
  const result = validateChatAttachmentFiles([file('large.jpg', 10 * mb + 1)])

  assert.equal(result.valid, false)
  assert.match(result.message, /单个文件不能超过 10MB/)
})

test('拒绝总大小超过 30MB 的聊天附件', () => {
  const result = validateChatAttachmentFiles([
    file('a.jpg', 10 * mb),
    file('b.jpg', 10 * mb),
    file('c.jpg', 10 * mb),
    file('d.jpg', 1),
  ])

  assert.equal(result.valid, false)
  assert.match(result.message, /文件总大小不能超过 30MB/)
})

test('允许符合数量和大小限制的聊天附件', () => {
  const result = validateChatAttachmentFiles([
    file('a.jpg', 2 * mb),
    file('b.jpg', 3 * mb),
  ])

  assert.equal(result.valid, true)
  assert.equal(result.message, '')
})
