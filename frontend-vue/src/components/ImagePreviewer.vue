<template>
  <Teleport to="body">
    <Transition name="image-preview-fade">
      <div
        v-if="previewVisible && previewSrc"
        class="image-preview-overlay"
        role="dialog"
        aria-modal="true"
        aria-label="图片预览"
        @click.self="closePreview"
      >
        <button type="button" class="image-preview-close" aria-label="关闭图片预览" @click="closePreview">
          ×
        </button>
        <div class="image-preview-stage">
          <img :src="previewSrc" alt="图片预览" class="image-preview-image" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'

const previewSrc = ref('')
const previewVisible = ref(false)
let clearPreviewTimer: ReturnType<typeof setTimeout> | null = null

function clearPendingTimer() {
  if (clearPreviewTimer) {
    clearTimeout(clearPreviewTimer)
    clearPreviewTimer = null
  }
}

function closePreview() {
  previewVisible.value = false
  clearPendingTimer()
  clearPreviewTimer = setTimeout(() => {
    previewSrc.value = ''
    clearPreviewTimer = null
  }, 200)
}

function onOpenImagePreview(e: Event) {
  const url = (e as CustomEvent<string>).detail
  if (!url) return

  clearPendingTimer()
  previewSrc.value = url
  previewVisible.value = true
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && previewVisible.value) {
    closePreview()
  }
}

watch(previewVisible, (visible) => {
  document.body.style.overflow = visible ? 'hidden' : ''
})

onMounted(() => {
  window.addEventListener('image-preview-open', onOpenImagePreview)
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  clearPendingTimer()
  document.body.style.overflow = ''
  window.removeEventListener('image-preview-open', onOpenImagePreview)
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.image-preview-overlay {
  position: fixed;
  inset: 0;
  z-index: 1600;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 28px;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.08), transparent 30%),
    rgba(10, 10, 12, 0.88);
  backdrop-filter: blur(14px);
}

.image-preview-stage {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: min(960px, calc(100vw - 180px));
  max-height: calc(100vh - 140px);
  padding: 0;
}

.image-preview-image {
  display: block;
  max-width: min(960px, calc(100vw - 180px));
  max-height: calc(100vh - 140px);
  object-fit: contain;
  border-radius: 18px;
  box-shadow:
    0 20px 70px rgba(0, 0, 0, 0.42),
    0 0 0 1px rgba(255, 255, 255, 0.1);
}

.image-preview-close {
  position: absolute;
  top: 22px;
  right: 24px;
  z-index: 1;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.9);
  font-size: 28px;
  line-height: 1;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.image-preview-close:hover {
  background: rgba(255, 255, 255, 0.16);
  transform: scale(1.04);
}

.image-preview-fade-enter-active,
.image-preview-fade-leave-active {
  transition: opacity 0.18s ease;
}

.image-preview-fade-enter-from,
.image-preview-fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .image-preview-overlay {
    padding: 20px 14px;
  }

  .image-preview-stage,
  .image-preview-image {
    max-width: calc(100vw - 28px);
    max-height: calc(100vh - 56px);
  }

  .image-preview-image {
    border-radius: 14px;
  }

  .image-preview-close {
    top: 14px;
    right: 14px;
  }
}
</style>
