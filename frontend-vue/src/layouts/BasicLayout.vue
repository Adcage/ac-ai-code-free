<template>
  <a-layout class="basic-layout">
    <GlobalHeader v-if="showGlobalChrome" />
    <a-layout-content class="layout-content" :class="{ 'layout-content-auth': !showGlobalChrome }">
      <RouterView />
    </a-layout-content>
    <GlobalFooter v-if="showGlobalChrome" />
  </a-layout>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import GlobalHeader from '@/components/GlobalHeader.vue'
import GlobalFooter from '@/components/GlobalFooter.vue'

const route = useRoute()
const showGlobalChrome = computed(() => route.meta.hideGlobalChrome !== true)
</script>

<style scoped>
.basic-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-content {
  flex: 1;
  background: var(--color-background);
  overflow-y: auto;
}

.layout-content-auth {
  overflow: hidden;
}
</style>
