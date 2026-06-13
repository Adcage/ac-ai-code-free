<template>
  <a-modal
    v-model:open="visible"
    title="编辑应用信息"
    :confirm-loading="confirmLoading"
    :maskClosable="false"
    @cancel="handleCancel"
    class="app-edit-modal"
  >
    <a-form :model="formState" layout="vertical" ref="formRef">
      <a-form-item
        label="应用名称"
        name="appName"
        :rules="[
          { required: true, message: '请输入应用名称' },
          { max: 80, message: '应用名称不能超过 80 个字符' },
        ]"
      >
        <a-input v-model:value="formState.appName" placeholder="请输入应用名称" />
      </a-form-item>

      <a-form-item v-if="isAdmin" label="应用封面" name="cover">
        <a-input v-model:value="formState.cover" placeholder="请输入封面图 URL" />
      </a-form-item>

      <a-form-item v-if="isAdmin" label="应用优先级" name="priority" extra="数值越大，在精选列表中排名越靠前">
        <a-input-number v-model:value="formState.priority" :min="0" style="width: 100%" />
      </a-form-item>

      <a-divider />

      <a-form-item label="风格模板" name="styleTemplate" v-if="formState.styleTemplate">
        <a-tag color="green">{{ formatStyleTemplate(formState.styleTemplate) }}</a-tag>
      </a-form-item>

      <a-form-item label="初始提示词" name="initPrompt" extra="初始提示词不可修改">
        <a-textarea v-model:value="formState.initPrompt" disabled :auto-size="{ minRows: 2, maxRows: 4 }" />
      </a-form-item>

      <a-form-item label="生成类型" name="codeGenType" extra="生成类型不可修改">
        <a-input :value="formatCodeGenType(formState.codeGenType)" disabled />
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
const initialData = ref<API.AppVO>()

interface FormState {
  id: number
  appName: string
  cover: string
  priority: number
  initPrompt: string
  codeGenType: string
  deployKey: string
  styleTemplate: string
}

const isAdmin = computed(() => loginUserStore.loginUser?.userRole === 'admin')

const formState = reactive<FormState>({
  id: 0,
  appName: '',
  cover: '',
  priority: 0,
  initPrompt: '',
  codeGenType: '',
  deployKey: '',
  styleTemplate: '',
})

const styleTemplateMap: Record<string, string> = {
  minimal: '极简风格',
  business: '商务风格',
  tech: '科技风格',
  playful: '活泼风格',
  dark: '暗黑风格',
}

const formatStyleTemplate = (template?: string) => {
  if (!template) return ''
  return styleTemplateMap[template] || template
}

const formatCodeGenType = (codeGenType?: string) => {
  if (codeGenType === 'single_file') return '单文件模式'
  if (codeGenType === 'multi-file') return '多文件模式'
  if (codeGenType === 'vue_project') return 'Vue 项目模式'
  return codeGenType || '未知模式'
}

const open = (app: API.AppVO) => {
  initialData.value = { ...app }
  formState.id = app.id || 0
  formState.appName = app.appName || ''
  formState.cover = app.cover || ''
  formState.priority = app.priority || 0
  formState.initPrompt = app.initPrompt || ''
  formState.codeGenType = app.codeGenType || ''
  formState.deployKey = app.deployKey || ''
  formState.styleTemplate = app.styleTemplate || ''
  visible.value = true
}

defineExpose({ open })

const handleReset = () => {
  if (initialData.value) {
    open(initialData.value)
  }
}

const goToApp = () => {
  visible.value = false
  router.push(`/app/generate/${formState.id}`)
}

const handleOk = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    confirmLoading.value = true

    const res = isAdmin.value
      ? await updateApp({ ...formState, id: formState.id as number })
      : await editApp({ id: formState.id as number, appName: formState.appName })

    if (res.data?.code === 0) {
      message.success('更新成功')
      visible.value = false
      emit('success')
    } else {
      message.error('更新失败，' + res.data?.message)
    }
  } catch {
    // validation failed
  } finally {
    confirmLoading.value = false
  }
}

const handleCancel = () => {
  visible.value = false
  formRef.value?.resetFields()
}
</script>

<style scoped>
.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.footer-left {
  display: flex;
  gap: var(--space-sm);
}
</style>
