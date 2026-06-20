<template>
  <div class="admin-page">
    <div class="page-container">
      <div class="page-header">
        <h1 class="page-title">应用管理</h1>
      </div>

      <div class="search-bar">
        <a-form layout="inline" :model="searchParams" @finish="doSearch">
          <a-form-item label="应用名称">
            <a-input v-model:value="searchParams.appName" placeholder="搜索应用名称" allow-clear class="search-input" />
          </a-form-item>
          <a-form-item label="生成类型">
            <a-select v-model:value="searchParams.codeGenType" placeholder="选择类型" style="width: 140px" allow-clear>
              <a-select-option value="single_file">单文件</a-select-option>
              <a-select-option value="multi-file">多文件</a-select-option>
              <a-select-option value="vue_project">Vue 项目</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="创建人">
            <a-input v-model:value="searchParams.userName" placeholder="搜索创建人" allow-clear class="search-input" />
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button type="primary" html-type="submit">
                <template #icon><Search :size="14" /></template>
                查询
              </a-button>
              <a-button @click="resetSearch">重置</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>

      <div class="table-wrapper">
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
            <template v-if="column.dataIndex === 'cover'">
              <a-image :src="record.cover" :width="50" style="border-radius: var(--radius-sm)" />
            </template>

            <template v-if="column.dataIndex === 'user'">
              <a-space v-if="record.user">
                <UserAvatar :user="record.user" size="small" />
                <span class="user-name">{{ record.user?.userName }}</span>
              </a-space>
              <span v-else class="text-muted">未知用户</span>
            </template>

            <template v-if="column.dataIndex === 'codeGenType'">
              <a-tag
                :color="
                  record.codeGenType === 'vue_project'
                    ? 'purple'
                    : record.codeGenType === 'multi-file'
                      ? 'cyan'
                      : 'green'
                "
              >
                {{ formatCodeGenType(record.codeGenType) }}
              </a-tag>
            </template>

            <template v-if="column.dataIndex === 'priority'">
              <a-tag v-if="record.priority >= 99" color="purple">精选</a-tag>
              <span v-else class="priority-text">{{ record.priority }}</span>
            </template>

            <template v-if="column.dataIndex === 'createTime'">
              <span class="time-text">{{ dayjs(record.createTime).format('YYYY-MM-DD HH:mm') }}</span>
            </template>

            <template v-if="column.key === 'action'">
              <div class="action-group">
                <a-button type="text" size="small" class="action-btn" @click="doEdit(record)">
                  <template #icon><Pencil :size="14" /></template>
                  编辑
                </a-button>
                <a-button
                  v-if="record.priority < 99"
                  type="text"
                  size="small"
                  class="action-btn featured-btn"
                  @click="doSetFeatured(record)"
                >
                  <template #icon><Star :size="14" /></template>
                  精选
                </a-button>
                <a-button
                  v-if="record.priority >= 99"
                  type="text"
                  size="small"
                  class="action-btn"
                  @click="doCancelFeatured(record)"
                >
                  <template #icon><Star :size="14" /></template>
                  取消精选
                </a-button>
                <a-popconfirm title="确定要删除吗？" ok-text="确定" cancel-text="取消" @confirm="doDelete(record.id)">
                  <a-button type="text" size="small" class="action-btn danger-action">
                    <template #icon><Trash2 :size="14" /></template>
                    删除
                  </a-button>
                </a-popconfirm>
              </div>
            </template>
          </template>
        </a-table>
      </div>
    </div>

    <AppEditModal ref="editModalRef" @success="loadData" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { Search, Pencil, Star, Trash2 } from '@lucide/vue'
import { listAppVoByPageByAdmin, deleteAppByAdmin, updateApp } from '@/api/appController'
import dayjs from 'dayjs'
import UserAvatar from '@/components/UserAvatar.vue'
import AppEditModal from '@/components/AppEditModal.vue'

const dataList = ref<API.AppVO[]>([])
const loading = ref(false)
const editModalRef = ref()

const searchParams = reactive<API.AppQueryRequest>({
  pageNum: 1,
  pageSize: 10,
  appName: '',
  codeGenType: undefined,
  userName: '',
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 180 },
  { title: '应用名称', dataIndex: 'appName', key: 'appName', ellipsis: true, width: 180 },
  { title: '封面', dataIndex: 'cover', key: 'cover', width: 80, align: 'center' },
  { title: '创建人', dataIndex: 'user', key: 'user', width: 150 },
  { title: '类型', dataIndex: 'codeGenType', key: 'codeGenType', width: 90, align: 'center' },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80, align: 'center' },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 160 },
  { title: '操作', key: 'action', width: 220, align: 'center' },
]

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

const formatCodeGenType = (codeGenType?: string) => {
  if (codeGenType === 'single_file') return '单文件'
  if (codeGenType === 'multi-file') return '多文件'
  if (codeGenType === 'vue_project') return 'Vue 项目'
  return codeGenType || '未知'
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await listAppVoByPageByAdmin(searchParams)
    const pageData = res.data?.data
    if (res.data?.code === 0 && pageData) {
      dataList.value = pageData.records || []
      pagination.total = Number(pageData.totalRow) || 0
    } else {
      message.error('加载失败，' + res.data?.message)
    }
  } catch (e: unknown) {
    message.error('加载失败，' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loading.value = false
  }
}

const doSearch = () => {
  searchParams.pageNum = 1
  loadData()
}

const resetSearch = () => {
  searchParams.appName = ''
  searchParams.codeGenType = undefined
  searchParams.userName = ''
  doSearch()
}

const handleTableChange = (pag: { current: number; pageSize: number }) => {
  searchParams.pageNum = pag.current
  searchParams.pageSize = pag.pageSize
  loadData()
}

const doDelete = async (id: number) => {
  const res = await deleteAppByAdmin({ id })
  if (res.data?.code === 0) {
    message.success('删除成功')
    loadData()
  } else {
    message.error('删除失败，' + res.data?.message)
  }
}

const doEdit = (record: API.AppVO) => {
  editModalRef.value?.open(record)
}

const doSetFeatured = async (record: API.AppVO) => {
  if (!record.id) {
    message.error('应用 ID 不存在，无法设置精选')
    return
  }
  const res = await updateApp({
    id: record.id as number,
    priority: 99,
  })
  if (res.data?.code === 0) {
    message.success('设置精选成功')
    loadData()
  } else {
    message.error('设置失败，' + res.data?.message)
  }
}

const doCancelFeatured = async (record: API.AppVO) => {
  if (!record.id) {
    message.error('应用 ID 不存在，无法取消精选')
    return
  }
  const res = await updateApp({
    id: record.id as number,
    priority: 0,
  })
  if (res.data?.code === 0) {
    message.success('取消精选成功')
    loadData()
  } else {
    message.error('取消失败，' + res.data?.message)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.admin-page {
  height: 100%;
  background: var(--color-background);
}

.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-lg);
}

.page-header {
  margin-bottom: var(--space-lg);
}

.page-title {
  font-family: var(--font-heading);
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.search-bar {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md) var(--space-lg);
  margin-bottom: var(--space-lg);
}

.search-input {
  width: 180px;
}

.table-wrapper {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.user-name {
  color: var(--color-text-secondary);
}

.text-muted {
  color: var(--color-text-muted);
}

.time-text {
  color: var(--color-text-muted);
  font-size: 13px;
}

.priority-text {
  color: var(--color-text-secondary);
}

.action-group {
  display: flex;
  gap: var(--space-xs);
  justify-content: center;
  align-items: center;
}

.action-btn {
  color: var(--color-text-secondary) !important;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.action-btn:hover {
  color: var(--color-cta) !important;
}

.featured-btn:hover {
  color: #a855f7 !important;
}

.danger-action:hover {
  color: var(--color-error) !important;
}

@media (max-width: 768px) {
  .page-container {
    padding: var(--space-lg) var(--space-md);
  }

  .page-title {
    font-size: 24px;
  }

  .search-input {
    width: 140px;
  }
}
</style>
