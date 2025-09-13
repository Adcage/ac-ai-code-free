<template>
  <a-layout class="basic-layout">
    <!-- 全局头部 -->
    <GlobalHeader />

    <!-- 主要内容区域 -->
    <a-layout-content class="layout-content">
      <RouterView />
    </a-layout-content>

    <!-- 全局底部 -->
    <GlobalFooter />
  </a-layout>
</template>

<script lang="ts" setup>
import { RouterView } from 'vue-router'
import GlobalHeader from '@/components/GlobalHeader.vue'
import GlobalFooter from '@/components/GlobalFooter.vue'
</script>

<style scoped>
.basic-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-content {
  flex: 1;
  padding: 24px;
  background: #fff;
}
</style>
