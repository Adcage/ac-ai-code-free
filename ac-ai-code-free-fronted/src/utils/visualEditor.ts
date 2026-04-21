export interface ElementInfo {
  tagName: string
  id: string
  className: string
  textContent: string
  selector: string
  pagePath: string
  rect: {
    top: number
    left: number
    width: number
    height: number
  }
}

type VisualEditorMessageType =
  | 'ELEMENT_HOVER'
  | 'ELEMENT_SELECTED'
  | 'TOGGLE_EDIT_MODE'
  | 'CLEAR_SELECTION'
  | 'CLEAR_ALL_EFFECTS'

interface VisualEditorMessage<T = unknown> {
  source: string
  type: VisualEditorMessageType
  payload?: T
}

interface CreateVisualEditorOptions {
  getIframe: () => HTMLIFrameElement | undefined
  onElementHover?: (element: ElementInfo | null) => void
  onElementSelected?: (element: ElementInfo | null) => void
  onModeChange?: (enabled: boolean) => void
}

const VISUAL_EDITOR_SOURCE = 'ACAICODEFREE_VISUAL_EDITOR'

const buildInjectedScript = () => {
  return `
  (() => {
    const SOURCE = '${VISUAL_EDITOR_SOURCE}'
    const STYLE_ID = '__ac_visual_editor_style__'
    const BANNER_ID = '__ac_visual_editor_banner__'
    const STATE_KEY = '__ACAICODEFREE_VISUAL_EDITOR_STATE__'
    const HOVER_CLASS = 'ac-visual-editor-hover'
    const SELECTED_CLASS = 'ac-visual-editor-selected'
    if (window[STATE_KEY]) {
      return
    }

    const state = {
      enabled: false,
      hoverElement: null,
      selectedElement: null,
      bannerElement: null,
    }
    window[STATE_KEY] = state

    const skipTags = new Set(['html', 'head', 'body', 'script', 'style', 'link', 'meta', 'title'])

    const normalizeText = (text) => {
      if (!text) {
        return ''
      }
      return String(text).replace(/\\s+/g, ' ').trim().slice(0, 120)
    }

    const escapeSelectorPart = (value) => {
      return String(value || '').replace(/[^a-zA-Z0-9_-]/g, '')
    }

    const buildSelector = (element) => {
      if (!element || !(element instanceof Element)) {
        return ''
      }
      const parts = []
      let current = element
      let depth = 0
      while (current && current.nodeType === 1 && depth < 8) {
        const tagName = current.tagName.toLowerCase()
        if (tagName === 'html') {
          break
        }
        if (tagName === 'body') {
          parts.unshift('body')
          break
        }

        let segment = tagName
        if (current.id) {
          segment += '#' + escapeSelectorPart(current.id)
          parts.unshift(segment)
          break
        }

        const classList = Array.from(current.classList || [])
          .map(escapeSelectorPart)
          .filter(Boolean)
          .slice(0, 2)
        if (classList.length) {
          segment += '.' + classList.join('.')
        }

        const parent = current.parentElement
        if (parent) {
          const sameTypeSiblings = Array.from(parent.children).filter((child) => child.tagName === current.tagName)
          if (sameTypeSiblings.length > 1) {
            segment += ':nth-of-type(' + (sameTypeSiblings.indexOf(current) + 1) + ')'
          }
        }

        parts.unshift(segment)
        current = current.parentElement
        depth += 1
      }

      return parts.join(' > ')
    }

    const collectElementInfo = (element) => {
      const rect = element.getBoundingClientRect()
      const className = typeof element.className === 'string' ? element.className : ''
      return {
        tagName: element.tagName.toLowerCase(),
        id: element.id || '',
        className,
        textContent: normalizeText(element.textContent),
        selector: buildSelector(element),
        pagePath: window.location.pathname + window.location.search,
        rect: {
          top: Number(rect.top.toFixed(2)),
          left: Number(rect.left.toFixed(2)),
          width: Number(rect.width.toFixed(2)),
          height: Number(rect.height.toFixed(2)),
        },
      }
    }

    const postToParent = (type, payload) => {
      window.parent.postMessage({
        source: SOURCE,
        type,
        payload,
      }, '*')
    }

    const ensureStyle = () => {
      if (document.getElementById(STYLE_ID)) {
        return
      }
      const styleElement = document.createElement('style')
      styleElement.id = STYLE_ID
      styleElement.textContent = [
        '.' + HOVER_CLASS + ' { outline: 2px dashed #1677ff !important; outline-offset: 1px !important; background-color: rgba(22, 119, 255, 0.08) !important; }',
        '.' + SELECTED_CLASS + ' { outline: 2px solid #52c41a !important; outline-offset: 1px !important; background-color: rgba(82, 196, 26, 0.12) !important; }',
      ].join('')
      document.head.appendChild(styleElement)
    }

    const ensureBanner = () => {
      if (state.bannerElement && document.body.contains(state.bannerElement)) {
        return state.bannerElement
      }
      let banner = document.getElementById(BANNER_ID)
      if (!banner) {
        banner = document.createElement('div')
        banner.id = BANNER_ID
        banner.textContent = '编辑模式已开启：悬浮查看，点击选中元素'
        banner.style.cssText = [
          'position: fixed',
          'top: 12px',
          'right: 12px',
          'z-index: 2147483647',
          'padding: 8px 10px',
          'font-size: 12px',
          'line-height: 1.4',
          'border-radius: 8px',
          'color: #0f172a',
          'background: rgba(255, 255, 255, 0.95)',
          'border: 1px solid rgba(148, 163, 184, 0.6)',
          'box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12)',
          'pointer-events: none',
        ].join(';')
        document.body.appendChild(banner)
      }
      state.bannerElement = banner
      return banner
    }

    const showBanner = () => {
      const banner = ensureBanner()
      if (banner) {
        banner.style.display = 'block'
      }
    }

    const hideBanner = () => {
      if (state.bannerElement) {
        state.bannerElement.style.display = 'none'
      }
    }

    const clearHover = () => {
      if (state.hoverElement) {
        state.hoverElement.classList.remove(HOVER_CLASS)
        state.hoverElement = null
      }
    }

    const clearSelected = () => {
      if (state.selectedElement) {
        state.selectedElement.classList.remove(SELECTED_CLASS)
        state.selectedElement = null
      }
    }

    const clearAllEffects = () => {
      clearHover()
      clearSelected()
    }

    const setHover = (element) => {
      if (state.hoverElement === element) {
        return
      }
      clearHover()
      if (element && element !== state.selectedElement) {
        element.classList.add(HOVER_CLASS)
        state.hoverElement = element
      }
    }

    const setSelected = (element) => {
      clearSelected()
      if (!element) {
        return
      }
      element.classList.add(SELECTED_CLASS)
      state.selectedElement = element
      if (state.hoverElement === element) {
        clearHover()
      }
    }

    const resolveTarget = (eventTarget) => {
      if (!(eventTarget instanceof Element)) {
        return null
      }
      if (eventTarget.closest('#' + BANNER_ID)) {
        return null
      }
      const tagName = eventTarget.tagName.toLowerCase()
      if (skipTags.has(tagName)) {
        return null
      }
      return eventTarget
    }

    const handleMouseOver = (event) => {
      if (!state.enabled) {
        return
      }
      const target = resolveTarget(event.target)
      if (!target) {
        clearHover()
        return
      }
      setHover(target)
      postToParent('ELEMENT_HOVER', collectElementInfo(target))
    }

    const handleMouseOut = (event) => {
      if (!state.enabled) {
        return
      }
      if (!(event.relatedTarget instanceof Element)) {
        clearHover()
        postToParent('ELEMENT_HOVER', null)
      }
    }

    const handleClick = (event) => {
      if (!state.enabled) {
        return
      }
      const target = resolveTarget(event.target)
      if (!target) {
        return
      }
      event.preventDefault()
      event.stopPropagation()
      if (typeof event.stopImmediatePropagation === 'function') {
        event.stopImmediatePropagation()
      }
      setSelected(target)
      postToParent('ELEMENT_SELECTED', collectElementInfo(target))
    }

    const handleMessage = (event) => {
      const data = event.data || {}
      if (!data || data.source !== SOURCE) {
        return
      }
      if (data.type === 'TOGGLE_EDIT_MODE') {
        state.enabled = !!(data.payload && data.payload.enabled)
        ensureStyle()
        if (state.enabled) {
          showBanner()
        } else {
          hideBanner()
          clearAllEffects()
          postToParent('ELEMENT_HOVER', null)
          postToParent('ELEMENT_SELECTED', null)
        }
        return
      }
      if (data.type === 'CLEAR_SELECTION') {
        clearSelected()
        postToParent('ELEMENT_SELECTED', null)
        return
      }
      if (data.type === 'CLEAR_ALL_EFFECTS') {
        clearAllEffects()
        postToParent('ELEMENT_HOVER', null)
        postToParent('ELEMENT_SELECTED', null)
      }
    }

    document.addEventListener('mouseover', handleMouseOver, true)
    document.addEventListener('mouseout', handleMouseOut, true)
    document.addEventListener('click', handleClick, true)
    window.addEventListener('message', handleMessage)
    ensureStyle()
  })();
  `
}

export const createVisualEditor = (options: CreateVisualEditorOptions) => {
  let isEditMode = false

  const postToIframe = (type: VisualEditorMessageType, payload?: unknown) => {
    const iframe = options.getIframe()
    const contentWindow = iframe?.contentWindow
    if (!contentWindow) {
      return false
    }
    const message: VisualEditorMessage = {
      source: VISUAL_EDITOR_SOURCE,
      type,
      payload,
    }
    contentWindow.postMessage(message, '*')
    return true
  }

  const ensureInjected = () => {
    const iframe = options.getIframe()
    if (!iframe?.contentDocument) {
      return false
    }
    try {
      const doc = iframe.contentDocument
      const markerId = '__ac_visual_editor_script__'
      if (doc.getElementById(markerId)) {
        return true
      }
      const scriptElement = doc.createElement('script')
      scriptElement.id = markerId
      scriptElement.type = 'text/javascript'
      scriptElement.text = buildInjectedScript()
      const target = doc.head || doc.body || doc.documentElement
      target.appendChild(scriptElement)
      return true
    } catch {
      return false
    }
  }

  const handleWindowMessage = (event: MessageEvent) => {
    const data = event.data as VisualEditorMessage<ElementInfo | null>
    if (!data || data.source !== VISUAL_EDITOR_SOURCE) {
      return
    }
    if (data.type === 'ELEMENT_HOVER') {
      options.onElementHover?.(data.payload ?? null)
    }
    if (data.type === 'ELEMENT_SELECTED') {
      options.onElementSelected?.(data.payload ?? null)
    }
  }

  window.addEventListener('message', handleWindowMessage)

  return {
    enterEditMode() {
      const injected = ensureInjected()
      if (!injected) {
        return false
      }
      isEditMode = true
      options.onModeChange?.(true)
      postToIframe('TOGGLE_EDIT_MODE', { enabled: true })
      return true
    },
    exitEditMode() {
      isEditMode = false
      options.onModeChange?.(false)
      postToIframe('TOGGLE_EDIT_MODE', { enabled: false })
      postToIframe('CLEAR_ALL_EFFECTS')
      options.onElementHover?.(null)
      options.onElementSelected?.(null)
    },
    clearSelection() {
      postToIframe('CLEAR_SELECTION')
      options.onElementSelected?.(null)
    },
    handleIframeLoad() {
      if (!isEditMode) {
        return
      }
      const injected = ensureInjected()
      if (!injected) {
        return
      }
      postToIframe('TOGGLE_EDIT_MODE', { enabled: true })
    },
    isEditMode() {
      return isEditMode
    },
    dispose() {
      window.removeEventListener('message', handleWindowMessage)
      isEditMode = false
    },
  }
}
