import type { RouteRecordRaw } from 'vue-router'

export default {
  path: '/pricing',
  name: 'pricing_layout',
  component: () => import('@/layouts/BasicLayout.vue'),
  children: [
    {
      path: '',
      name: '价格',
      component: () => import('@/pages/pricing/PricingPage.vue'),
    },
  ],
} as RouteRecordRaw
