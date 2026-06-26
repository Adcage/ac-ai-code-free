/**
 * SSE 请求工具
 *
 * 对标 request.ts（myAxios），为 SSE 流式请求提供统一的：
 * - baseURL（复用 myAxios 配置）
 * - withCredentials（复用 myAxios 配置）
 * - 401 拦截（跳登录页）
 * - 错误消息提示
 *
 * SSE 为什么不能用 myAxios？
 * myAxios 底层使用 XMLHttpRequest，会缓冲整个响应体后才 resolve，
 * 拿不到流式的 chunk。SSE 必须使用 fetch + response.body.getReader()。
 */
import { message } from 'ant-design-vue'
import myAxios from '@/request'
import router from '@/router'

export interface SseRequestOptions {
  /** 请求路径（相对于 baseURL） */
  path: string
  /** POST JSON body */
  body?: Record<string, unknown>
  /** AbortSignal，用于取消请求 */
  signal?: AbortSignal
}

/**
 * SSE POST 请求
 * 返回 fetch Response，调用方通过 response.body.getReader() 读取流。
 */
export async function ssePost(options: SseRequestOptions): Promise<Response> {
  const { path, body, signal } = options
  const baseURL = myAxios.defaults.baseURL || import.meta.env.VITE_API_BASE_URL || ''
  const withCredentials = myAxios.defaults.withCredentials !== false

  const response = await fetch(`${baseURL}${path}`, {
    method: 'POST',
    credentials: withCredentials ? 'include' : 'omit',
    cache: 'no-store',
    signal,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })

  // 401 → 跳登录（与 myAxios 响应拦截器一致）
  if (response.status === 401) {
    if (!window.location.pathname.includes('/user/login')) {
      message.warning('请先登录')
      router.push({ path: '/user/login', query: { redirect: window.location.pathname } })
    }
    throw new Error('未登录')
  }

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || `HTTP ${response.status}`)
  }

  return response
}
