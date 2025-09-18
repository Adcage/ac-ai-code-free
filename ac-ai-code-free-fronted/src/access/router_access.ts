import { useLoginUserStore } from '@/stores/LoginUser.ts'
import { message } from 'ant-design-vue'
import router from '@/router'

// 是否为首次获取登录用户
let firstFetchLoginUser = true

/**
 * 全局权限校验
 * 注意：前端权限控制仅用于改善用户体验，真正的安全控制必须在后端实现
 */
router.beforeEach(async (to, from, next) => {
  const loginUserStore = useLoginUserStore()
  let loginUser = loginUserStore.loginUser
  // 确保页面刷新，首次加载时，能够等后端返回用户信息后再校验权限
  if (firstFetchLoginUser) {
    await loginUserStore.fetchLoginUser()
    loginUser = loginUserStore.loginUser
    firstFetchLoginUser = false
  }
  // 使用fullPath，可以保留路由访问参数，path只保留路径
  // fullPath示例: /admin/user?id=123  path示例: /admin/user
  const toUrl = to.fullPath
  // 当界面为 管理员 界面
  if (toUrl.startsWith('/admin')) {
    // 未登录
    if (loginUser.userName === '未登录') {
      message.error('未登录，请先登录')
      next(`/user/login?redirect=${to.fullPath}`)
      return
    }
    // 无管理员权限
    if (loginUser.userRole !== 'admin') {
      message.error('没有权限')
      next(from.fullPath)
      return
    }
  }
  next()
})