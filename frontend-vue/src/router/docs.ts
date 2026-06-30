import type { RouteRecordRaw } from 'vue-router'

export default {
  path: '/docs',
  name: 'docs_layout',
  component: () => import('@/layouts/BasicLayout.vue'),
  children: [
    {
      path: '',
      name: '文档',
      component: () => import('@/pages/docs/DocsPage.vue'),
    },
  ],
} as RouteRecordRaw
