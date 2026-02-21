<template>
  <a-modal
    v-model:open="visible"
    title="编辑应用信息"
    :confirm-loading="confirmLoading"
    :maskClosable="false"
    @cancel="handleCancel"
  >
    <a-form :model="formState" layout="vertical" ref="formRef">
      <a-form-item
        label="应用名称"
        name="appName"
        :rules="[
          { required: true, message: '请输入应用名称' },
          { max: 80, message: '应用名称不能超过 80 个字符' }
        ]"
      >
        <a-input v-model:value="formState.appName" placeholder="请输入应用名称" />
      </a-form-item>

      <a-form-item v-if="isAdmin" label="应用封面" name="cover">
        <a-input v-model:value="formState.cover" placeholder="请输入封面图 URL" />
      </a-form-item>

      <a-form-item
        v-if="isAdmin"
        label="应用优先级"
        name="priority"
        extra="数值越大，在精选列表中排名越靠前"
      >
        <a-input-number v-model:value="formState.priority" :min="0" style="width: 100%" />
      </a-form-item>

      <a-divider />

      <!-- 只读展示字段 -->
      <a-form-item label="初始提示词" name="initPrompt" extra="初始提示词不可修改">
        <a-textarea v-model:value="formState.initPrompt" disabled :auto-size="{ minRows: 2, maxRows: 4 }" />
      </a-form-item>

      <a-form-item label="生成类型" name="codeGenType" extra="生成类型不可修改">
        <a-input v-model:value="formState.codeGenType" disabled />
      </a-form-item>

      <a-form-item label="部署密钥" name="deployKey" extra="部署密钥不可修改">
        <a-input v-model:value="formState.deployKey" disabled />
      </a-form-item>
    </a-form>

    <template #footer>
      <div class="modal-footer">
        <div class="footer-left">
          <a-button type="primary" @click="handleOk" :loading="confirmLoading">保存修改</a-button>
          <a-button @click="handleReset">重置</a-button>
        </div>
        <a-button type="link" @click="goToApp">进入对话</a-button>
      </div>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { editApp, updateApp } from '@/api/appController'
import { useLoginUserStore } from '@/stores/LoginUser'

const emit = defineEmits(['success'])
const loginUserStore = useLoginUserStore()
const router = useRouter()

const visible = ref(false)
const confirmLoading = ref(false)
const formRef = ref()
const initialData = ref<API.AppVO>() // 用于重置

const isAdmin = computed(() => loginUserStore.loginUser?.userRole === 'admin')

const formState = reactive<any>({
  id: 0,
  appName: '',
  cover: '',
  priority: 0,
  initPrompt: '',
  codeGenType: '',
  deployKey: '',
})

/**
 * 暴露给父组件的打开方法
 */
const open = (app: API.AppVO) => {
  initialData.value = { ...app }
  formState.id = app.id || 0
  formState.appName = app.appName || ''
  formState.cover = app.cover || ''
  formState.priority = app.priority || 0
  formState.initPrompt = app.initPrompt || ''
  formState.codeGenType = app.codeGenType || ''
  formState.deployKey = app.deployKey || ''
  visible.value = true
}

defineExpose({ open })

/**
 * 重置表单
 */
const handleReset = () => {
  if (initialData.value) {
    open(initialData.value)
  }
}

/**
 * 进入对话
 */
const goToApp = () => {
  visible.value = false
  router.push(`/app/generate/${formState.id}`)
}

/**
 * 提交表单
 */
const handleOk = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    confirmLoading.value = true
    
    // 管理员使用 updateApp，普通用户使用 editApp
    const res = isAdmin.value 
      ? await updateApp(formState) 
      : await editApp({ id: formState.id, appName: formState.appName })

    if (res.data?.code === 0) {
      message.success('更新成功')
      visible.value = false
      emit('success')
    } else {
      message.error('更新失败，' + res.data?.message)
    }
  } catch (error) {
    // 校验失败
  } finally {
    confirmLoading.value = false
  }
}

/**
 * 取消处理
 */
const handleCancel = () => {
  visible.value = false
  formRef.value?.resetFields()
}
</script>

<style scoped>
.tip {
  margin-top: 16px;
  color: #bfbfbf;
  font-size: 12px;
  background: #fafafa;
  padding: 8px 12px;
  border-radius: 8px;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.footer-left {
  display: flex;
  gap: 8px;
}
</style>
