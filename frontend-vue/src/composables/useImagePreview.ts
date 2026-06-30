import { ref } from 'vue'

export interface ImagePreviewApi {
  readonly previewUrl: { value: string }
  readonly isOpen: { value: boolean }
  openPreview(url: string): void
  closePreview(): void
}

const previewUrl = ref('')
const isOpen = ref(false)

function openPreview(url: string) {
  previewUrl.value = url
  isOpen.value = true
}

function closePreview() {
  previewUrl.value = ''
  isOpen.value = false
}

export { previewUrl, isOpen, openPreview, closePreview }

export function useImagePreview(): ImagePreviewApi {
  return { previewUrl, isOpen, openPreview, closePreview }
}

export function createImagePreviewStore(): ImagePreviewApi {
  return { previewUrl, isOpen, openPreview, closePreview }
}
