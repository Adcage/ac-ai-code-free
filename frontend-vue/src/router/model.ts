import type { RouteRecordRaw } from 'vue-router'
import ModelConfigPage from '@/pages/model/ModelConfigPage.vue'

export default [
  {
    path: '/model/config',
    name: 'model_config',
    component: ModelConfigPage,
    meta: {
      name: '模型配置',
    },
  },
] as Array<RouteRecordRaw>
