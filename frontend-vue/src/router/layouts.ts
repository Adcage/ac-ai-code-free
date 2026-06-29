import type { RouteRecordRaw } from 'vue-router'

export default {
  path: '/',
  component: () => import('@/layouts/BasicLayout.vue'),
  children: [
    {
      path: '',
      name: '主页',
      component: () => import('@/pages/HomePage.vue'),
    },
    {
      path: 'app/my',
      name: 'my_apps',
      component: () => import('@/pages/app/MyAppListPage.vue'),
    },
    {
      path: 'app/generate/:id',
      name: 'app_generate',
      component: () => import('@/pages/app/AppGeneratorPage.vue'),
      meta: {
        hideInMenu: true,
      },
    },
    {
      path: 'app/edit/:id',
      redirect: '/app/my',
    },
    {
      path: 'user/register',
      name: '注册',
      component: () => import('@/pages/user/UserRegisterPage.vue'),
      meta: {
        hideGlobalChrome: true,
      },
    },
    {
      path: 'user/login',
      name: '登录',
      component: () => import('@/pages/user/UserLoginPage.vue'),
      meta: {
        hideGlobalChrome: true,
      },
    },
    {
      path: 'user/profile',
      name: '个人中心',
      component: () => import('@/pages/user/UserProfilePage.vue'),
    },
    {
      path: 'user/usage',
      name: '用量统计',
      component: () => import('@/pages/user/TokenDashboardPage.vue'),
    },
    {
      path: 'user/settings',
      name: '账号设置',
      component: () => import('@/pages/user/UserSettingsPage.vue'),
    },
  ],
} as RouteRecordRaw
