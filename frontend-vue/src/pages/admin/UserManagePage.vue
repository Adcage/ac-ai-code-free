<template>
  <div class="admin-page">
    <div class="page-container">
      <div class="page-header">
        <h1 class="page-title">用户管理</h1>
      </div>

      <div class="search-bar">
        <a-form layout="inline" :model="searchParams" @finish="doSearch">
          <a-form-item label="账号">
            <a-input v-model:value="searchParams.userAccount" placeholder="搜索账号" allow-clear class="search-input" />
          </a-form-item>
          <a-form-item label="用户名">
            <a-input v-model:value="searchParams.userName" placeholder="搜索用户名" allow-clear class="search-input" />
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button type="primary" html-type="submit">
                <template #icon><Search :size="14" /></template>
                查询
              </a-button>
              <a-button @click="resetSearch">重置</a-button>
              <a-popconfirm v-if="selectedRowKeys.length > 0" title="确定要批量删除这些用户吗？" @confirm="multiDelete">
                <a-button danger>
                  <template #icon><Trash2 :size="14" /></template>
                  批量删除 ({{ selectedRowKeys.length }})
                </a-button>
              </a-popconfirm>
            </a-space>
          </a-form-item>
        </a-form>
      </div>

      <div class="table-wrapper">
        <a-table
          :columns="columns"
          :data-source="dataList"
          :pagination="pagination"
          :row-selection="rowSelection"
          :loading="loading"
          size="middle"
          row-key="id"
          @change="doTableChange"
        >
          <template #bodyCell="{ column, text, record }">
            <template v-if="column.key === 'userName'">
              <a-input v-if="editableData[record.id]" v-model:value="editableData[record.id].userName" size="small" />
              <span v-else>{{ text }}</span>
            </template>

            <template v-if="column.key === 'userAvatar'">
              <UserAvatar :user="record" size="small" />
            </template>

            <template v-if="column.key === 'userRole'">
              <a-select
                v-if="editableData[record.id]"
                v-model:value="editableData[record.id].userRole"
                style="width: 100%"
                size="small"
              >
                <a-select-option value="admin">管理员</a-select-option>
                <a-select-option value="user">普通用户</a-select-option>
              </a-select>
              <template v-else>
                <a-tag v-if="record.userRole === 'admin'" color="green">管理员</a-tag>
                <a-tag v-else color="blue">普通用户</a-tag>
              </template>
            </template>

            <template v-else-if="column.key === 'createTime'">
              <span class="time-text">{{ dayjs(record.createTime).format('YYYY-MM-DD HH:mm') }}</span>
            </template>

            <template v-else-if="column.key === 'action'">
              <div v-if="!editableData[record.id]" class="action-group">
                <a-button type="text" size="small" class="action-btn" @click="edit(record)">
                  <template #icon><Pencil :size="14" /></template>
                  编辑
                </a-button>
                <a-popconfirm
                  title="确定要删除吗？"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleDelete(record.id)"
                >
                  <a-button type="text" size="small" class="action-btn danger-action">
                    <template #icon><Trash2 :size="14" /></template>
                    删除
                  </a-button>
                </a-popconfirm>
              </div>
              <div v-else class="action-group">
                <a-button type="text" size="small" class="action-btn" @click="save(record.id)"> 保存 </a-button>
                <a-button type="text" size="small" class="action-btn" @click="cancel(record.id)"> 取消 </a-button>
              </div>
            </template>
          </template>
        </a-table>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { deleteUser, listUserByPage, updateUser, multiDeleteUser } from '@/api/userController'
import dayjs from 'dayjs'
import type { TableProps } from 'ant-design-vue'
import { message } from 'ant-design-vue'
import { Search, Pencil, Trash2 } from '@lucide/vue'
import UserAvatar from '@/components/UserAvatar.vue'

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 180 },
  { title: '账号', dataIndex: 'userAccount', key: 'userAccount', ellipsis: true },
  { title: '用户名', dataIndex: 'userName', key: 'userName', width: 150, ellipsis: true },
  { title: '头像', dataIndex: 'userAvatar', key: 'userAvatar', width: 80, align: 'center' },
  { title: '角色', dataIndex: 'userRole', key: 'userRole', width: 120, align: 'center' },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 160 },
  { title: '操作', key: 'action', width: 160, align: 'center' },
]

const dataList = ref<API.User[]>([])
const total = ref(0)
const loading = ref(false)

const searchParams = reactive<API.UserQueryRequest>({
  pageNum: 1,
  pageSize: 10,
  userName: '',
  userAccount: '',
})

const pagination = computed(() => ({
  current: searchParams.pageNum ?? 1,
  pageSize: searchParams.pageSize ?? 10,
  total: total.value,
  showSizeChanger: true,
  showTotal: (t: number) => `共 ${t} 条`,
}))

const selectedRowKeys = ref<(string | number)[]>([])
const rowSelection = computed<TableProps['rowSelection']>(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: (string | number)[]) => {
    selectedRowKeys.value = keys
  },
}))

const editableData = reactive<Record<number, API.User>>({})

const fetchData = async () => {
  loading.value = true
  try {
    const res = await listUserByPage(searchParams)
    if (res.data?.code === 0) {
      dataList.value = res.data.data?.records || []
      total.value = res.data.data?.totalRow || 0
    }
  } finally {
    loading.value = false
  }
}

const doTableChange = (page: { current: number; pageSize: number }) => {
  searchParams.pageNum = page.current
  searchParams.pageSize = page.pageSize
  fetchData()
}

const doSearch = () => {
  searchParams.pageNum = 1
  fetchData()
}

const resetSearch = () => {
  searchParams.userName = ''
  searchParams.userAccount = ''
  doSearch()
}

const handleDelete = async (id: number) => {
  const res = await deleteUser({ id })
  if (res.data?.code === 0) {
    message.success('删除成功')
    fetchData()
  } else {
    message.error('删除失败，' + res.data?.message)
  }
}

const multiDelete = async () => {
  if (selectedRowKeys.value.length === 0) return
  const deleteBody = selectedRowKeys.value.map((id) => ({ id: Number(id) }))
  const res = await multiDeleteUser(deleteBody)
  if (res.data?.code === 0) {
    message.success('批量删除成功')
    selectedRowKeys.value = []
    fetchData()
  } else {
    message.error('批量删除失败，' + res.data?.message)
  }
}

const edit = (rowData: API.User) => {
  if (rowData.id) {
    editableData[rowData.id] = JSON.parse(JSON.stringify(rowData))
  }
}

const save = async (id: number) => {
  const res = await updateUser(editableData[id])
  if (res.data?.code === 0) {
    message.success('编辑成功')
    delete editableData[id]
    fetchData()
  } else {
    message.error('修改失败，' + res.data?.message)
  }
}

const cancel = (id: number) => {
  delete editableData[id]
}

onMounted(() => {
  fetchData()
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

.time-text {
  color: var(--color-text-muted);
  font-size: 13px;
}

.action-group {
  display: flex;
  gap: var(--space-xs);
  justify-content: center;
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
