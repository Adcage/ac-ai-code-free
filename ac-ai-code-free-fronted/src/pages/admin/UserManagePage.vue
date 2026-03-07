<template>
  <div id="userManagePage">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
    </div>

    <div class="search-card">
      <a-form layout="inline" :model="searchParams" @finish="doSearch">
        <a-form-item label="用户账号">
          <a-input v-model:value="searchParams.userAccount" placeholder="请输入账号" allow-clear />
        </a-form-item>
        <a-form-item label="用户名">
          <a-input v-model:value="searchParams.userName" placeholder="请输入用户名" allow-clear />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit">查询</a-button>
            <a-button @click="resetSearch">重置</a-button>
            <a-popconfirm
              v-if="selectedRow.length > 0"
              title="确定要批量删除这些用户吗？"
              @confirm="multiDelete"
            >
              <a-button danger>批量删除 ({{ selectedRow.length }})</a-button>
            </a-popconfirm>
          </a-space>
        </a-form-item>
      </a-form>
    </div>

    <div class="table-card">
      <a-table
        :columns="columns"
        :data-source="dataList"
        :pagination="pagination"
        :row-selection="rowSelection"
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
            <a-image :src="record.userAvatar" :width="40" style="border-radius: 50%" />
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
              <a-select-option value="vip">VIP</a-select-option>
            </a-select>
            <template v-else>
              <a-tag v-if="record.userRole === 'admin'" color="green">管理员</a-tag>
              <a-tag v-else-if="record.userRole === 'vip'" color="orange">VIP</a-tag>
              <a-tag v-else color="blue">普通用户</a-tag>
            </template>
          </template>

          <template v-else-if="column.key === 'createTime'">
            <span class="time-text">{{ dayjs(record.createTime).format('YYYY-MM-DD HH:mm:ss') }}</span>
          </template>
          
          <template v-else-if="column.key === 'updateTime'">
            <span class="time-text">{{ dayjs(record.updateTime).format('YYYY-MM-DD HH:mm:ss') }}</span>
          </template>

          <template v-else-if="column.key === 'action'">
            <div v-if="!editableData[record.id]" class="action-slots">
              <div class="action-slot">
                <a-button type="link" size="small" @click="edit(record)">编辑</a-button>
              </div>
              <div class="action-slot">
                <a-popconfirm title="确定要删除吗？" ok-text="确定" cancel-text="取消" @confirm="handleDelete(record.id)">
                  <a-button type="link" size="small" danger>删除</a-button>
                </a-popconfirm>
              </div>
            </div>
            <div v-else class="action-slots">
              <div class="action-slot">
                <a-button type="link" size="small" @click="save(record.id)">保存</a-button>
              </div>
              <div class="action-slot">
                <a-button type="link" size="small" @click="cancel(record.id)" style="color: #666">取消</a-button>
              </div>
            </div>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { deleteUser, listUserByPage, updateUser } from '@/api/userController'
import dayjs from 'dayjs'
import type { TableProps } from 'ant-design-vue'
import { message } from 'ant-design-vue'

// 表格列表内容
const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 180 },
  { title: '账号', dataIndex: 'userAccount', key: 'userAccount', ellipsis: true },
  { title: '用户名', dataIndex: 'userName', key: 'userName', width: 150, ellipsis: true },
  { title: '头像', dataIndex: 'userAvatar', key: 'userAvatar', width: 80, align: 'center' },
  { title: '角色', dataIndex: 'userRole', key: 'userRole', width: 120, align: 'center' },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '更新时间', dataIndex: 'updateTime', key: 'updateTime', width: 180 },
  { title: '操作', key: 'action', width: 160, align: 'center' },
]

const dataList = ref<API.User[]>([])
const total = ref(0)
const loading = ref(false)

// 搜索条件
const searchParams = reactive<API.UserQueryRequest>({
  pageNum: 1,
  pageSize: 10,
  userName: '',
  userAccount: '',
})

// 分页
const pagination = computed(() => ({
  current: searchParams.pageNum ?? 1,
  pageSize: searchParams.pageSize ?? 10,
  total: total.value,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
}))

// 表格多选
const selectedRow = ref<number[]>([])
const rowSelection: TableProps['rowSelection'] = {
  onChange: (selectedRowKeys) => {
    selectedRow.value = selectedRowKeys as number[]
  },
}

// 可编辑数据
const editableData = reactive<Record<number, API.User>>({})

// 请求用户数据
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

const doTableChange = (page: any) => {
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
  // 批量删除接口暂未对接，此处可预留
  message.info('批量删除功能开发中')
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
#userManagePage {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: calc(100vh - 64px);
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 0;
}

.search-card {
  background: #fff;
  padding: 24px;
  border-radius: 4px;
  margin-bottom: 16px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.table-card {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.time-text {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}

.action-slots {
  display: flex;
  justify-content: center;
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
