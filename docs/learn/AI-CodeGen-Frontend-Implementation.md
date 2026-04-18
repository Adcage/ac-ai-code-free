# AI 编程辅助平台前端实现学习文档

本手册记录了 `ac-ai-code-free` 前端核心模块的实现逻辑、技术难点及避坑指南。

## 1. 核心架构与技术栈

- **框架**: Vue 3 (Composition API + Setup)
- **UI 组件库**: Ant Design Vue 4.x (企业级 UI)
- **样式方案**: Tailwind CSS (原子类快速布局)
- **通信**: Axios (普通接口) + EventSource (SSE 流式对话)
- **预览**: Iframe (跨域静态资源加载)

## 2. 技术要点深度解析

### 2.1 SSE (Server-Sent Events) 流式处理
SSE 是实现 AI 对话实时感的关键技术。相比 WebSocket，它更轻量（基于 HTTP），适合单向数据流。

**实现关键点**：
- **原生 EventSource**: 浏览器内置支持。注意：如果需要自定义 Header（如 Bearer Token），建议使用 `fetch-event-source` 库。
- **双层解析（兼容模式）**: 外层始终先解析 `data: {"d": "..."}`；老模式把 `d` 当纯文本，`vue_project` 模式再对 `d` 做二次 `JSON.parse`。
- **消息类型处理**: `ai_response` 直接拼接自然语言；`tool_request` 展示“准备写入文件”；`tool_executed` 展示“已写入文件”。
- **状态管理**: 增加 `generating` 标识。在 `onmessage` 收到 `[DONE]` 或 `onerror` 时，务必 `close()` 连接并重置状态。
- **自动滚动**: 利用 `nextTick` 和 `scrollTop = scrollHeight` 确保新消息出现时页面自动沉底。

### 2.2 跨端口资源预览 (Iframe)
本项目中，预览服务和 API 均运行在 `8700` 端口。

**要点**：
- **URL 构造分支**:
  - 老模式：`/api/static/{codeGenType}_{appId}/index.html`
  - `vue_project`：`/api/static/vue_project_{appId}/dist/index.html`
- **缓存解决**: 在 URL 后追加 `?t=${Date.now()}` 强制 Iframe 刷新，否则多次生成后浏览器可能会加载旧缓存。
- **响应式预览**: 通过 CSS 动态调整 Iframe 容器宽度（如 `max-width: 375px`）模拟移动端效果。

### 3.2 动态 Iframe 预览刷新
处理生成后的预览展示，关键在于“时间戳”解决缓存问题。

```typescript
const updatePreview = () => {
  const codeGenType = app.value?.codeGenType || 'single_file'
  if (codeGenType === 'vue_project') {
    iframeUrl.value = `/api/static/vue_project_${appId}/dist/index.html?t=${Date.now()}`
    return
  }
  iframeUrl.value = `/api/static/${codeGenType}_${appId}/index.html?t=${Date.now()}`
}
```

### 3.3 创建应用请求契约

创建应用时必须显式传入：

```typescript
addApp({
  initPrompt: searchText.value,
  codeGenType: 'vue_project',
})
```

否则后端会按参数错误处理，前后端模式会不一致。

### 3.3 响应式列表渲染 (Ant Design Vue)
主页中“我的作品”列表的实现，展示了 Grid 布局的使用。

```html
<a-list
  :grid="{ gutter: 24, xs: 1, sm: 2, md: 3, lg: 3, xl: 3, xxl: 3 }"
  :data-source="myAppList"
>
  <template #renderItem="{ item }">
    <a-list-item>
      <a-card hoverable class="app-card" @click="goToApp(item.id)">
        <template #cover>
          <img :src="item.cover || defaultCover" class="card-cover" />
        </template>
        <a-card-meta :title="item.appName">
          <template #description>
            创建于 {{ formatDate(item.createTime) }}
          </template>
        </a-card-meta>
      </a-card>
    </a-list-item>
  </template>
</a-list>
```

## 4. 常见问题与避坑指南

| 现象 | 原因 | 解决方法 |
| :--- | :--- | :--- |
| **SSE 报错 400** | 参数名不匹配 | 严格对照 API 文档。如本例中应使用 `message` 而非 `userMessage`。 |
| **SSE 报错 404/Connection Refused** | 端口号错误 | 后端 API 与静态预览服务通常在不同端口，EventSource 必须指向 API 端口。 |
| **界面显示 JSON 源码** | 未解析响应体 | SSE 传输的是字符串，必须手动 `JSON.parse`。 |
| **对话结束显示“连接中断”** | `onerror` 误报 | SSE 正常关闭有时会触发 error 事件。在 `onerror` 中判断是否已完成，若是则静默关闭。 |

## 4. UI/UX 优化建议
- **渐变背景**: 使用 Tailwind 的 `bg-gradient-to-br` 配合浅色系（emerald, blue, slate）可以营造现代感。
- **输入交互**: 监听 `pressEnter` 事件（不带 Shift）触发发送，符合主流聊天工具（WeChat/Slack）习惯。
- **Skeleton 屏/空状态**: 在 Iframe 加载完成前，提供有设计感的占位图（Empty 状态），避免页面显得突兀。

---
*文档生成日期: 2026-02-14*
