import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { baseParse, NodeTypes } from '@vue/compiler-dom'
import { parse } from '@vue/compiler-sfc'

function collectElementTags(node: any, tags: string[] = []): string[] {
  if (node.type === NodeTypes.ELEMENT) {
    tags.push(node.tag)
  }

  if ('children' in node && Array.isArray(node.children)) {
    for (const child of node.children) {
      collectElementTags(child, tags)
    }
  }

  return tags
}

test('ImagePreviewer 使用自定义灯箱而不是 a-modal 或 a-image', () => {
  const source = readFileSync(new URL('../src/components/ImagePreviewer.vue', import.meta.url), 'utf8')
  const { descriptor } = parse(source)

  assert.ok(descriptor.template?.content, 'ImagePreviewer 应包含 template')

  const ast = baseParse(descriptor.template.content)
  const tags = collectElementTags(ast)

  assert.ok(!tags.includes('a-modal'), '图片预览不应再使用 a-modal 承载大图预览')
  assert.ok(!tags.includes('a-image'), '图片预览不应再使用 a-image 作为隐藏触发器')
  assert.match(source, /image-preview-overlay/, '图片预览应包含全屏灯箱遮罩结构')
  assert.match(source, /image-preview-stage/, '图片预览应包含图片舞台容器结构')
})

test('聊天消息与上传区使用内容化图片卡片类名', () => {
  const chatMessageListSource = readFileSync(new URL('../src/components/ChatMessageList.vue', import.meta.url), 'utf8')
  const chatInputAreaSource = readFileSync(new URL('../src/components/ChatInputArea.vue', import.meta.url), 'utf8')

  assert.match(chatMessageListSource, /attachment-image-card/, '聊天消息中的图片应使用内容化卡片类名')
  assert.match(chatInputAreaSource, /upload-image-card/, '上传区图片应使用统一的卡片类名')
})

test('聊天图片缩略图与预览舞台尺寸保持克制', () => {
  const chatMessageListSource = readFileSync(new URL('../src/components/ChatMessageList.vue', import.meta.url), 'utf8')
  const imagePreviewerSource = readFileSync(new URL('../src/components/ImagePreviewer.vue', import.meta.url), 'utf8')

  assert.match(
    chatMessageListSource,
    /width:\s*clamp\(64px,\s*14vw,\s*112px\)/,
    '聊天图片缩略图应收敛到更接近 GPT 的小卡片宽度',
  )
  assert.match(
    chatMessageListSource,
    /aspect-ratio:\s*1\s*\/\s*1/,
    '聊天图片缩略图应使用更轻量的方形预览比例',
  )
  assert.match(
    imagePreviewerSource,
    /max-width:\s*min\(960px,\s*calc\(100vw - 180px\)\)/,
    '图片预览舞台应比当前更克制，避免大图铺满屏幕',
  )
})

test('用户图片消息应与文本气泡分层，而不是继续包在 message-content 里', () => {
  const chatMessageListSource = readFileSync(new URL('../src/components/ChatMessageList.vue', import.meta.url), 'utf8')

  assert.match(chatMessageListSource, /user-message-media/, '用户消息图片应有独立媒体容器')
  assert.match(chatMessageListSource, /user-message-bubble/, '用户消息文本应有独立气泡容器')
})
