<template>
  <div class="model-config-page">
    <div class="page-container">
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">模型配置</h1>
          <p class="page-desc">管理你的 AI 模型和 API 接入配置</p>
        </div>
        <a-button type="primary" class="create-btn" @click="openAddModal">
          <template #icon><Plus :size="16" /></template>
          新增配置
        </a-button>
      </div>

      <div v-if="loading" class="loading-state">
        <a-spin size="large" />
      </div>

      <div v-else-if="dataList.length === 0" class="empty-state">
        <div class="empty-icon"><Settings :size="64" /></div>
        <h3 class="empty-title">暂无模型配置</h3>
        <p class="empty-desc">添加一个模型配置开始使用 AI 功能</p>
        <a-button type="primary" class="create-btn" @click="openAddModal">
          <template #icon><Plus :size="16" /></template>
          新增配置
        </a-button>
      </div>

      <div v-else class="config-grid">
        <div v-for="item in dataList" :key="item.id" :class="['config-card', { 'config-disabled': !item.enabled }]">
          <div class="card-header">
            <div class="card-title-row">
              <h3 class="config-name">{{ item.modelName }}</h3>
              <a-tag v-if="item.isDefault" color="success" class="default-tag">默认</a-tag>
            </div>
            <div class="provider-tag">{{ item.provider }}</div>
          </div>

          <div class="card-body">
            <div class="config-detail">
              <span class="detail-label">Base URL</span>
              <span class="detail-value url-text" :title="item.baseUrl">{{ item.baseUrl || '-' }}</span>
            </div>
            <div class="config-params">
              <div class="param-item">
                <Thermometer :size="14" class="param-icon" />
                <span class="param-label">Temperature</span>
                <span class="param-value">{{ item.temperature ?? '-' }}</span>
              </div>
              <div class="param-item">
                <Hash :size="14" class="param-icon" />
                <span class="param-label">Max Tokens</span>
                <span class="param-value">{{ item.maxTokens ?? '-' }}</span>
              </div>
            </div>
          </div>

          <div class="card-actions">
            <div class="actions-left">
              <a-switch
                :checked="item.enabled === 1"
                checked-children="开"
                un-checked-children="关"
                @change="(checked: boolean) => toggleEnabled(item, checked)"
              />
              <a-button
                v-if="item.isDefault !== 1"
                type="text"
                size="small"
                class="action-text-btn"
                @click="setDefault(item)"
              >
                <template #icon><Star :size="14" /></template>
                设为默认
              </a-button>
            </div>
            <div class="actions-right">
              <a-button type="text" size="small" class="action-text-btn" @click="openEditModal(item)">
                <template #icon><Pencil :size="14" /></template>
                编辑
              </a-button>
              <a-popconfirm
                title="确定要删除该配置吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDelete(item.id!)"
              >
                <a-button type="text" size="small" class="action-text-btn danger-btn">
                  <template #icon><Trash2 :size="14" /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </div>
          </div>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑配置' : '新增配置'"
      :confirm-loading="submitLoading"
      ok-text="保存"
      cancel-text="取消"
      @ok="handleSubmit"
      @cancel="resetForm"
      class="config-modal"
    >
      <a-form ref="formRef" :model="formData" :rules="formRules" layout="vertical" style="margin-top: var(--space-md)">
        <a-form-item label="供应商" name="provider">
          <a-select
            v-if="!isEdit"
            v-model:value="formData.provider"
            placeholder="选择或输入供应商"
            :options="providerOptions"
            show-search
            allow-clear
          />
          <a-input v-else v-model:value="formData.provider" placeholder="如 openai、deepseek" />
        </a-form-item>
        <a-form-item label="模型名称" name="modelName">
          <a-input v-model:value="formData.modelName" placeholder="如 deepseek-chat" />
        </a-form-item>
        <a-form-item label="Base URL" name="baseUrl">
          <a-input v-model:value="formData.baseUrl" placeholder="如 https://api.deepseek.com" />
        </a-form-item>
        <a-form-item label="API Key" name="apiKeyCipher">
          <a-input-password
            v-model:value="formData.apiKeyCipher"
            :placeholder="isEdit ? '留空则不修改' : '请输入 API Key'"
          />
        </a-form-item>
        <a-form-item label="Temperature" name="temperature">
          <a-slider
            v-model:value="formData.temperature"
            :min="0"
            :max="2"
            :step="0.1"
            :marks="{ 0: '0', 0.7: '0.7', 2: '2' }"
          />
        </a-form-item>
        <a-form-item label="Max Tokens" name="maxTokens">
          <a-input-number v-model:value="formData.maxTokens" :min="1" :max="128000" :step="1024" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import { Plus, Settings, Star, Pencil, Trash2, Thermometer, Hash } from '@lucide/vue'
import request from '@/request'

interface ModelConfigVO {
  id?: number
  provider?: string
  modelName?: string
  baseUrl?: string
  apiKeyCipher?: string
  temperature?: number
  maxTokens?: number
  configVersion?: number
  enabled?: number
  isDefault?: number
  createTime?: string
  updateTime?: string
}

interface ModelConfigAddRequest {
  provider: string
  modelName: string
  baseUrl: string
  apiKeyCipher: string
  temperature?: number
  maxTokens?: number
}

interface ModelConfigEditRequest {
  id: number
  provider?: string
  modelName?: string
  baseUrl?: string
  apiKeyCipher?: string
  temperature?: number
  maxTokens?: number
}

interface ModelConfigQueryRequest {
  pageNum?: number
  pageSize?: number
}

interface PageResult<T> {
  records?: T[]
  totalRow?: number
  pageNumber?: number
  pageSize?: number
}

const providerOptions = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'zhipu', label: '智谱 AI' },
  { value: 'qwen', label: '通义千问' },
  { value: 'moonshot', label: 'Moonshot' },
  { value: 'yi', label: '零一万物' },
  { value: 'baichuan', label: '百川智能' },
  { value: 'minimax', label: 'MiniMax' },
  { value: 'spark', label: '讯飞星火' },
]

const dataList = ref<ModelConfigVO[]>([])
const loading = ref(false)
const total = ref(0)

const searchParams = reactive<ModelConfigQueryRequest>({
  pageNum: 1,
  pageSize: 100,
})

const modalVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const editingId = ref<number>()

const formRef = ref<FormInstance>()

const defaultFormData = (): ModelConfigAddRequest & { id?: number } => ({
  provider: '',
  modelName: '',
  baseUrl: '',
  apiKeyCipher: '',
  temperature: 0.7,
  maxTokens: 8192,
})

const formData = reactive(defaultFormData())

const formRules: Record<string, Rule[]> = {
  provider: [{ required: true, message: '请选择或输入供应商' }],
  modelName: [{ required: true, message: '请输入模型名称' }],
  baseUrl: [{ required: true, message: '请输入 Base URL' }],
  apiKeyCipher: [{ required: true, message: '请输入 API Key' }],
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.post<{ code: number; data?: PageResult<ModelConfigVO>; message?: string }>(
      '/model-config/my/list/page/vo',
      searchParams,
    )
    if (res.data?.code === 0 && res.data.data) {
      dataList.value = res.data.data.records || []
      total.value = res.data.data.totalRow || 0
    } else {
      message.error('加载失败，' + (res.data?.message ?? ''))
    }
  } catch (e: unknown) {
    message.error('加载失败，' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  isEdit.value = false
  editingId.value = undefined
  Object.assign(formData, defaultFormData())
  modalVisible.value = true
}

const openEditModal = (record: ModelConfigVO) => {
  isEdit.value = true
  editingId.value = record.id
  Object.assign(formData, {
    provider: record.provider ?? '',
    modelName: record.modelName ?? '',
    baseUrl: record.baseUrl ?? '',
    apiKeyCipher: '',
    temperature: record.temperature ?? 0.7,
    maxTokens: record.maxTokens ?? 8192,
  })
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validateFields()
  } catch {
    return
  }

  submitLoading.value = true
  try {
    if (isEdit.value && editingId.value) {
      const editData: ModelConfigEditRequest = {
        id: editingId.value,
        provider: formData.provider,
        modelName: formData.modelName,
        baseUrl: formData.baseUrl,
        temperature: formData.temperature,
        maxTokens: formData.maxTokens,
      }
      if (formData.apiKeyCipher) {
        editData.apiKeyCipher = formData.apiKeyCipher
      }
      const res = await request.post<{ code: number; data?: boolean; message?: string }>('/model-config/edit', editData)
      if (res.data?.code === 0) {
        message.success('编辑成功')
        modalVisible.value = false
        fetchData()
      } else {
        message.error('编辑失败，' + (res.data?.message ?? ''))
      }
    } else {
      const res = await request.post<{ code: number; data?: number; message?: string }>('/model-config/add', formData)
      if (res.data?.code === 0) {
        message.success('添加成功')
        modalVisible.value = false
        fetchData()
      } else {
        message.error('添加失败，' + (res.data?.message ?? ''))
      }
    }
  } catch (e: unknown) {
    message.error('操作失败，' + (e instanceof Error ? e.message : String(e)))
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  formRef.value?.resetFields()
}

const handleDelete = async (id: number) => {
  const res = await request.post<{ code: number; data?: boolean; message?: string }>('/model-config/delete', { id })
  if (res.data?.code === 0) {
    message.success('删除成功')
    fetchData()
  } else {
    message.error('删除失败，' + (res.data?.message ?? ''))
  }
}

const toggleEnabled = async (record: ModelConfigVO, checked: boolean) => {
  const res = await request.post<{ code: number; data?: boolean; message?: string }>('/model-config/toggle/enabled', {
    id: record.id,
  })
  if (res.data?.code === 0) {
    message.success(checked ? '已启用' : '已禁用')
    fetchData()
  } else {
    message.error('操作失败，' + (res.data?.message ?? ''))
  }
}

const setDefault = async (record: ModelConfigVO) => {
  const res = await request.post<{ code: number; data?: boolean; message?: string }>('/model-config/set/default', {
    id: record.id,
  })
  if (res.data?.code === 0) {
    message.success('已设为默认')
    fetchData()
  } else {
    message.error('设置失败，' + (res.data?.message ?? ''))
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.model-config-page {
  min-height: calc(100vh - 64px);
  background: var(--color-background);
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-lg);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-2xl);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.page-title {
  font-family: var(--font-heading);
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.page-desc {
  font-size: 15px;
  color: var(--color-text-muted);
  margin: 0;
}

.create-btn {
  background: var(--color-cta) !important;
  border-color: var(--color-cta) !important;
  font-weight: 600;
  height: 40px;
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.create-btn:hover {
  background: var(--color-cta-hover) !important;
  border-color: var(--color-cta-hover) !important;
  transform: translateY(-1px);
}

.loading-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.empty-icon {
  color: var(--color-text-muted);
  margin-bottom: var(--space-lg);
  opacity: 0.5;
}

.empty-title {
  font-family: var(--font-heading);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-sm);
}

.empty-desc {
  font-size: 16px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-xl);
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
}

.config-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  transition: all var(--transition-normal);
}

.config-card:hover {
  border-color: var(--color-border-light);
  box-shadow: var(--shadow-md);
}

.config-disabled {
  opacity: 0.55;
}

.config-disabled:hover {
  opacity: 0.75;
}

.card-header {
  margin-bottom: var(--space-md);
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.config-name {
  font-family: var(--font-heading);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.default-tag {
  font-weight: 600;
}

.provider-tag {
  display: inline-block;
  padding: 2px 10px;
  background: var(--color-surface-elevated);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
}

.card-body {
  margin-bottom: var(--space-md);
}

.config-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: var(--space-md);
}

.detail-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.detail-value {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.url-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.config-params {
  display: flex;
  gap: var(--space-lg);
}

.param-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.param-icon {
  color: var(--color-text-muted);
}

.param-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.param-value {
  font-size: 13px;
  color: var(--color-text);
  font-weight: 500;
  font-family: var(--font-heading);
}

.card-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
}

.actions-left,
.actions-right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.action-text-btn {
  color: var(--color-text-secondary) !important;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.action-text-btn:hover {
  color: var(--color-cta) !important;
}

.danger-btn:hover {
  color: var(--color-error) !important;
}

@media (max-width: 768px) {
  .page-container {
    padding: var(--space-lg) var(--space-md);
  }

  .page-header {
    flex-direction: column;
    gap: var(--space-md);
    align-items: flex-start;
  }

  .config-grid {
    grid-template-columns: 1fr;
  }

  .page-title {
    font-size: 24px;
  }

  .card-actions {
    flex-direction: column;
    gap: var(--space-sm);
    align-items: flex-start;
  }
}
</style>
