import test from 'node:test'
import assert from 'node:assert/strict'
import { useImagePreview } from '../src/composables/useImagePreview'

test('初始状态没有预览 URL', () => {
  const store = useImagePreview()

  assert.equal(store.previewUrl.value, '')
  assert.equal(store.isOpen.value, false)
})

test('openPreview 设置 URL 并打开预览', () => {
  // 先关掉之前可能的状态
  const store = useImagePreview()
  store.closePreview()

  store.openPreview('http://localhost:8700/api/storage/x.jpg')

  assert.equal(store.previewUrl.value, 'http://localhost:8700/api/storage/x.jpg')
  assert.equal(store.isOpen.value, true)

  // 清理
  store.closePreview()
})

test('closePreview 清空 URL 并关闭预览', () => {
  const store = useImagePreview()
  store.openPreview('http://localhost:8700/api/storage/x.jpg')

  store.closePreview()

  assert.equal(store.previewUrl.value, '')
  assert.equal(store.isOpen.value, false)
})

test('多次调用 useImagePreview 返回同一状态', () => {
  useImagePreview().closePreview()

  const a = useImagePreview()
  const b = useImagePreview()

  a.openPreview('http://localhost:8700/api/storage/x.jpg')

  assert.equal(b.previewUrl.value, 'http://localhost:8700/api/storage/x.jpg')
  assert.equal(b.isOpen.value, true)

  // 清理
  a.closePreview()
})
