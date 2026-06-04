import type { RouteRecordRaw } from 'vue-router'
import UserRegisterPage from '@/pages/user/UserRegisterPage.vue'
import UserLoginPage from '@/pages/user/UserLoginPage.vue'

export default [
  {
    path: '/user/register',
    name: '注册',
    component: UserRegisterPage
  },
  {
    path: '/user/login',
    name: '登录',
    component: UserLoginPage
  }
] as Array<RouteRecordRaw>
