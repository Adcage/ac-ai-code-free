import test from 'node:test'
import assert from 'node:assert/strict'

const BASE_URL = process.env.E2E_API_BASE_URL || 'http://127.0.0.1:8700/api'

async function postJson(path, body, cookie) {
  const headers = { 'Content-Type': 'application/json' }
  if (cookie) {
    headers.Cookie = cookie
  }
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  })
  const text = await response.text()
  let data
  try {
    data = JSON.parse(text)
  } catch {
    data = { raw: text }
  }
  return { response, data }
}

async function getJson(path, cookie) {
  const headers = {}
  if (cookie) {
    headers.Cookie = cookie
  }
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'GET',
    headers,
  })
  const text = await response.text()
  let data
  try {
    data = JSON.parse(text)
  } catch {
    data = { raw: text }
  }
  return { response, data }
}

async function readSseFrames(sseResponse, options = {}) {
  const reader = sseResponse.body?.getReader()
  assert.ok(reader, 'SSE 响应流为空')
  const decoder = new TextDecoder('utf-8')
  const deadline = Date.now() + (options.timeoutMs || 30000)
  let buffer = ''
  while (Date.now() < deadline) {
    const { done, value } = await reader.read()
    if (done) {
      break
    }
    buffer += decoder.decode(value, { stream: true })
    if (buffer.includes('event:done')) {
      break
    }
  }
  await reader.cancel()
  return buffer
}

function extractSseDataLines(sseText) {
  return sseText
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.replace(/^data:\s*/, ''))
    .filter((line) => line.length > 0)
}

async function runChatFlow({ codeGenType, prompt, message, assertSse }) {
  const suffix = `${Date.now()}_${Math.floor(Math.random() * 100000)}`
  const userAccount = `e2e_front_${suffix}`
  const userPassword = '12345678'

  const registerRes = await postJson('/user/register', {
    userAccount,
    userPassword,
    checkPassword: userPassword,
  })
  assert.equal(registerRes.data.code, 0, `注册失败: ${JSON.stringify(registerRes.data)}`)

  const loginRes = await postJson('/user/login', {
    userAccount,
    userPassword,
  })
  assert.equal(loginRes.data.code, 0, `登录失败: ${JSON.stringify(loginRes.data)}`)
  const cookie = loginRes.response.headers.get('set-cookie')
  assert.ok(cookie, '登录后未拿到会话 Cookie')

  const addAppBody = {
    initPrompt: prompt,
    ...(codeGenType ? { codeGenType } : {}),
  }
  const addAppRes = await postJson('/app/add', addAppBody, cookie)
  assert.equal(addAppRes.data.code, 0, `创建应用失败: ${JSON.stringify(addAppRes.data)}`)
  const appId = addAppRes.data.data
  assert.ok(appId, '创建应用未返回 appId')

  const appDetailRes = await getJson(`/app/get/vo?id=${appId}`, cookie)
  assert.equal(appDetailRes.data.code, 0, `查询应用详情失败: ${JSON.stringify(appDetailRes.data)}`)
  assert.ok(appDetailRes.data?.data?.codeGenType, '创建应用后应有生成类型')

  try {
    const createSessionRes = await postJson('/app/chat/session/create', { appId }, cookie)
    assert.equal(createSessionRes.data.code, 0, `创建会话失败: ${JSON.stringify(createSessionRes.data)}`)
    const sessionId = String(createSessionRes.data.data)
    assert.ok(/^\d+$/.test(sessionId), '创建会话未返回合法 sessionId')

    const sseResponse = await fetch(`${BASE_URL}/app/chat/gen/code/stream`, {
      method: 'POST',
      headers: {
        Cookie: cookie,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        appId,
        sessionId,
        message,
      }),
    })
    assert.equal(sseResponse.status, 200, `SSE 响应码异常: ${sseResponse.status}`)
    const contentType = sseResponse.headers.get('content-type') || ''
    if (!contentType.includes('text/event-stream')) {
      const abnormalBody = await sseResponse.text()
      assert.fail(`SSE Content-Type 异常: ${contentType}; body: ${abnormalBody}`)
    }

    const sseText = await readSseFrames(sseResponse)
    assert.equal(sseText.includes('event:meta'), true, `SSE 缺少 meta 事件: ${sseText}`)
    assert.equal(sseText.includes(`"sessionId":${sessionId}`), true, `SSE meta 未返回正确 sessionId: ${sseText}`)
    await assertSse(sseText)

    const listSessionRes = await getJson(`/app/chat/session/list?appId=${appId}`, cookie)
    assert.equal(listSessionRes.data.code, 0, `会话列表查询失败: ${JSON.stringify(listSessionRes.data)}`)
    const currentSession = (listSessionRes.data.data || []).find((item) => String(item.id) === sessionId)
    assert.ok(currentSession, '会话列表中不存在刚创建的会话')

    await new Promise((resolve) => setTimeout(resolve, 500))
    const historyRes = await postJson(
      '/app/chat/history/page',
      {
        appId,
        sessionId,
        pageNum: 1,
        pageSize: 20,
      },
      cookie,
    )
    assert.equal(historyRes.data.code, 0, `历史分页查询失败: ${JSON.stringify(historyRes.data)}`)
    const records = historyRes.data?.data?.records || []
    assert.ok(records.length >= 1, '历史消息为空，至少应包含用户消息')
    assert.equal(records[0].messageType, 'user', '首条历史消息应为用户消息')

    const downloadResponse = await fetch(`${BASE_URL}/app/download/${appId}`, {
      method: 'GET',
      headers: { Cookie: cookie },
    })
    assert.equal(downloadResponse.status, 200, `源码下载失败: ${downloadResponse.status}`)
    const downloadContentType = downloadResponse.headers.get('content-type') || ''
    assert.ok(downloadContentType.includes('application/zip'), `源码下载类型错误: ${downloadContentType}`)
    const zipBuffer = Buffer.from(await downloadResponse.arrayBuffer())
    assert.ok(zipBuffer.length > 0, '下载 ZIP 内容为空')
  } finally {
    await postJson('/app/delete', { id: appId }, cookie)
    await postJson('/user/logout', {}, cookie)
  }
}

test('前端到后端聊天链路端到端：登录 -> 应用 -> 会话 -> SSE -> 历史', async () => {
  await runChatFlow({
    codeGenType: undefined,
    prompt: '请生成一个按钮页面',
    message: '请生成一个蓝色按钮',
    assertSse: async (sseText) => {
      assert.equal(sseText.includes('event:meta'), true)
    },
  })
})

test('前端到后端聊天链路端到端：vue_project SSE 二层消息契约可兼容', async () => {
  await runChatFlow({
    codeGenType: 'vue_project',
    prompt: '请生成一个 Vue3 单页应用',
    message: '请先创建基础项目结构',
    assertSse: async (sseText) => {
      const dataLines = extractSseDataLines(sseText)
      const nonEmptyPayloads = dataLines.filter((line) => line !== '[DONE]')
      assert.ok(nonEmptyPayloads.length >= 1, `SSE 未返回有效数据帧: ${sseText}`)

      let hasOuterEnvelope = false
      for (const payload of nonEmptyPayloads) {
        try {
          const outer = JSON.parse(payload)
          if (typeof outer.d === 'string') {
            hasOuterEnvelope = true
            if (outer.d.startsWith('{')) {
              const inner = JSON.parse(outer.d)
              assert.ok(
                ['ai_response', 'tool_request', 'tool_executed'].includes(inner.type) || typeof inner.type === 'undefined',
                `vue_project 内层消息类型异常: ${outer.d}`,
              )
            }
          }
        } catch {
          // 兼容极端场景：服务端已中断，仅要求至少存在可解析 envelope
        }
      }

      assert.equal(hasOuterEnvelope, true, `SSE 未返回标准外层 envelope: ${sseText}`)
    },
  })
})

test('前端到后端聊天链路端到端：可视化选区上下文修改请求可通过', async () => {
  await runChatFlow({
    codeGenType: 'single_file',
    prompt: '请生成一个包含标题和按钮的页面',
    message: `选中元素信息：\n- 页面路径：/\n- 标签：h1\n- 选择器：div.hero > h1\n- 当前内容：你好\n\n修改需求：把标题改成“欢迎访问”`,
    assertSse: async (sseText) => {
      assert.equal(sseText.includes('event:meta'), true)
      assert.equal(sseText.includes('event:done'), true)
    },
  })
})
