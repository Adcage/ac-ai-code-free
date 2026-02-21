<template>
  <div id="appEditPage">
    <a-card title="修改应用信息" :bordered="false">
      <a-form 
        :model="form" 
        layout="vertical" 
        @finish="handleSubmit"
        style="max-width: 600px"
      >
        <a-form-item label="应用名称" name="appName" :rules="[{ required: true, message: '请输入应用名称' }]">
          <a-input v-model:value="form.appName" placeholder="请输入应用名称" />
        </a-form-item>
        
        <a-form-item label="应用封面" name="cover" v-if="isAdmin">
          <a-input v-model:value="form.cover" placeholder="请输入封面图片 URL" />
          <a-image v-if="form.cover" :src="form.cover" :width="200" style="margin-top: 8px" />
        </a-form-item>

        <a-form-item label="优先级" name="priority" v-if="isAdmin">
          <a-input-number v-model:value="form.priority" :min="0" :max="100" />
        </a-form-item>

        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="submitting">保存修改</a-button>
            <a-button @click="router.back()">返回</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getAppVoById, editApp, updateApp } from '@/api/appController'
import { useLoginUserStore } from '@/stores/LoginUser'

const route = useRoute()
const router = useRouter()
const loginUserStore = useLoginUserStore()
const appId = route.params.id as string
const submitting = ref(false)

const isAdmin = computed(() => loginUserStore.loginUser.userRole === 'admin')

const form = ref<any>({
  appName: '',
  cover: '',
  priority: 0
})

const loadData = async () => {
  const res = await getAppVoById({ id: appId as any })
  if (res.data?.code === 0) {
    const data = res.data.data
    form.value = {
      appName: data.appName,
      cover: data.cover,
      priority: data.priority
    }
  }
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    let res
    if (isAdmin.value) {
      res = await updateApp({ id: appId as any, ...form.value })
    } else {
      res = await editApp({ id: appId as any, appName: form.value.appName })
    }
    
    if (res.data?.code === 0) {
      message.success('修改成功')
      router.back()
    } else {
      message.error('修改失败，' + res.data?.message)
    }
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
#appEditPage {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}
</style>
