<template>
  <a-avatar :src="avatarSrc" :size="size" class="user-avatar">
    <template #icon v-if="!avatarSrc"><UserOutlined /></template>
  </a-avatar>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { UserOutlined } from '@ant-design/icons-vue'

interface Props {
  src?: string
  user?: any
  size?: number | 'large' | 'small' | 'default'
}

const props = defineProps<Props>()

const avatarSrc = computed(() => {
  if (props.src) return props.src
  if (props.user?.userAvatar) return props.user.userAvatar
  return ''
})
</script>

<style scoped>
.user-avatar {
  background-color: #1890ff;
  color: #fff;
  flex-shrink: 0;
}
</style>
