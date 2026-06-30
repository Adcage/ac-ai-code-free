import test from 'node:test'
import assert from 'node:assert/strict'
import { createJiti } from 'jiti'

const jiti = createJiti(import.meta.url, {
  interopDefault: true,
  moduleCache: false,
})

const routeRecord = jiti('../src/router/layouts.ts')
const userChildren = routeRecord.children ?? []

const loginRoute = userChildren.find((item: any) => item.path === 'user/login')
const registerRoute = userChildren.find((item: any) => item.path === 'user/register')

test('认证路由应隐藏全局头尾', () => {
  assert.equal(loginRoute?.meta?.hideGlobalChrome, true)
  assert.equal(registerRoute?.meta?.hideGlobalChrome, true)
})
