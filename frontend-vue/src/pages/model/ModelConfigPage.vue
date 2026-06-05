<template>
  <div id="modelConfigPage">
    <div class="page-header">
      <h2 class="page-title">模型配置</h2>
      <a-button type="primary" @click="openAddModal">添加配置</a-button>
    </div>

    <div class="table-card">
      <a-table
        :columns="columns"
        :data-source="dataList"
        :pagination="pagination"
        :loading="loading"
        size="middle"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'provider'">
            <a-tag color="blue">{{ record.provider }}</a-tag>
          </template>

          <template v-if="column.dataIndex === 'apiKeyCipher'">
            <span class="masked-key">••••••••</span>
          </template>

          <template v-if="column.dataIndex === 'temperature'">
            {{ record.temperature ?? '-' }}
          </template>

          <template v-if="column.dataIndex === 'maxTokens'">
            {{ record.maxTokens ?? '-' }}
          </template>

          <template v-if="column.dataIndex === 'enabled'">
            <a-switch
              :checked="record.enabled"
              checked-children="开"
              un-checked-children="关"
              @change="(checked: boolean) => toggleEnabled(record, checked)"
            />
          </template>

          <template v-if="column.dataIndex === 'isDefault'">
            <a-tag v-if="record.isDefault" color="green">默认</a-tag>
            <a-button v-else type="link" size="small" @click="setDefault(record)">设为默认</a-button>
          </template>

          <template v-if="column.dataIndex === 'createTime'">
            <span class="time-text">{{ dayjs(record.createTime).format('YYYY-MM-DD HH:mm:ss') }}</span>
          </template>

          <template v-if="column.key === 'action'">
            <div class="action-slots">
              <div class="action-slot">
                <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
              </div>
              <div class="action-slot">
                <a-popconfirm
                  title="确定要删除该配置吗？"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleDelete(record.id)"
                >
                  <a-button type="link" size="small" danger>删除</a-button>
                </a-popconfirm>
              </div>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑配置' : '添加配置'"
      :confirm-loading="submitLoading"
      ok-text="确定"
      cancel-text="取消"
      @ok="handleSubmit"
      @cancel="resetForm"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
        style="margin-top: 16px"
      >
        <a-form-item label="Provider" name="provider">
          <a-input v-model:value="formData.provider" placeholder="如 openai、deepseek" />
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
          <a-input-number
            v-model:value="formData.temperature"
            :min="0"
            :max="2"
            :step="0.1"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="Max Tokens" name="maxTokens">
          <a-input-number
            v-model:value="formData.maxTokens"
            :min="1"
            :max="128000"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'
import dayjs from 'dayjs'
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
  enabled?: boolean
  isDefault?: boolean
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

const columns = [
  { title: 'Provider', dataIndex: 'provider', key: 'provider', width: 110 },
  { title: '模型名称', dataIndex: 'modelName', key: 'modelName', width: 150, ellipsis: true },
  { title: 'Base URL', dataIndex: 'baseUrl', key: 'baseUrl', width: 200, ellipsis: true },
  { title: 'API Key', dataIndex: 'apiKeyCipher', key: 'apiKeyCipher', width: 110, align: 'center' },
  { title: 'Temperature', dataIndex: 'temperature', key: 'temperature', width: 100, align: 'center' },
  { title: 'Max Tokens', dataIndex: 'maxTokens', key: 'maxTokens', width: 110, align: 'center' },
  { title: '版本', dataIndex: 'configVersion', key: 'configVersion', width: 70, align: 'center' },
  { title: '启用', dataIndex: 'enabled', key: 'enabled', width: 90, align: 'center' },
  { title: '默认', dataIndex: 'isDefault', key: 'isDefault', width: 90, align: 'center' },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 170 },
  { title: '操作', key: 'action', width: 140, align: 'center', fixed: 'right' },
]

const dataList = ref<ModelConfigVO[]>([])
const loading = ref(false)
const total = ref(0)

const searchParams = reactive<ModelConfigQueryRequest>({
  pageNum: 1,
  pageSize: 10,
})

const pagination = computed(() => ({
  current: searchParams.pageNum ?? 1,
  pageSize: searchParams.pageSize ?? 10,
  total: total.value,
  showSizeChanger: true,
  showTotal: (t: number) => `共 ${t} 条`,
}))

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
  provider: [{ required: true, message: '请输入 Provider' }],
  modelName: [{ required: true, message: '请输入模型名称' }],
  baseUrl: [{ required: true, message: '请输入 Base URL' }],
  apiKeyCipher: [{ required: true, message: '请输入 API Key' }],
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await request.post<{ code: number; data?: PageResult<ModelConfigVO>; message?: string }>(
      '/model_config/my/list/page/vo',
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

const handleTableChange = (pag: { current: number; pageSize: number }) => {
  searchParams.pageNum = pag.current
  searchParams.pageSize = pag.pageSize
  fetchData()
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
      const res = await request.post<{ code: number; data?: boolean; message?: string }>(
        '/model_config/edit',
        editData,
      )
      if (res.data?.code === 0) {
        message.success('编辑成功')
        modalVisible.value = false
        fetchData()
      } else {
        message.error('编辑失败，' + (res.data?.message ?? ''))
      }
    } else {
      const res = await request.post<{ code: number; data?: number; message?: string }>(
        '/model_config/add',
        formData,
      )
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
  const res = await request.post<{ code: number; data?: boolean; message?: string }>(
    '/model_config/delete',
    { id },
  )
  if (res.data?.code === 0) {
    message.success('删除成功')
    fetchData()
  } else {
    message.error('删除失败，' + (res.data?.message ?? ''))
  }
}

const toggleEnabled = async (record: ModelConfigVO, checked: boolean) => {
  const res = await request.post<{ code: number; data?: boolean; message?: string }>(
    '/model_config/toggle/enabled',
    { id: record.id, enabled: checked },
  )
  if (res.data?.code === 0) {
    message.success(checked ? '已启用' : '已禁用')
    fetchData()
  } else {
    message.error('操作失败，' + (res.data?.message ?? ''))
  }
}

const setDefault = async (record: ModelConfigVO) => {
  const res = await request.post<{ code: number; data?: boolean; message?: string }>(
    '/model_config/set/default',
    { id: record.id },
  )
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
#modelConfigPage {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 64px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 0;
}

.table-card {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.masked-key {
  color: rgba(0, 0, 0, 0.45);
  letter-spacing: 2px;
}

.time-text {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}

.action-slots {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.action-slot {
  width: 50px;
  display: flex;
  justify-content: center;
}

:deep(.ant-table-thead > tr > th) {
  background-color: #fafafa;
  font-weight: 500;
}
</style>
