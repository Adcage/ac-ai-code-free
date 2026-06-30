import type { RouteRecordRaw } from 'vue-router'

export default {
  path: '/explore',
  name: 'explore_layout',
  component: () => import('@/layouts/BasicLayout.vue'),
  children: [
    {
      path: '',
      name: '探索广场',
      component: () => import('@/pages/explore/ExplorePage.vue'),
    },
  ],
} as RouteRecordRaw
