import type { RouteRecordRaw } from 'vue-router'
import UserManagePage from '@/pages/admin/UserManagePage.vue'

export default [
  {
    path: '/admin/userManage',
    name: 'admin',
    component: UserManagePage
  }
] as Array<RouteRecordRaw>
