<template>
  <div id="appAdminPage">
    <div class="header">
      <h2>应用管理</h2>
    </div>
    <a-form layout="inline" :model="searchParams" class="search-form" @finish="doSearch">
      <a-form-item label="应用名称">
        <a-input v-model:value="searchParams.appName" placeholder="请输入应用名称" allow-clear />
      </a-form-item>
      <a-form-item label="用户 ID">
        <a-input v-model:value="searchParams.userId" placeholder="请输入创建人 ID" allow-clear />
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit">查询</a-button>
        <a-button style="margin-left: 8px" @click="resetSearch">重置</a-button>
      </a-form-item>
    </a-form>
    <a-table
      :columns="columns"
      :data-source="dataList"
      :pagination="pagination"
      :loading="loading"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'cover'">
          <a-image :src="record.cover" :width="60" />
        </template>
        <template v-if="column.dataIndex === 'user'">
          <a-space>
            <a-avatar :src="record.user?.userAvatar" size="small" />
            {{ record.user?.userName }}
          </a-space>
        </template>
        <template v-if="column.dataIndex === 'priority'">
          <a-tag :color="record.priority >= 99 ? 'purple' : 'blue'">
            {{ record.priority }}
          </a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="link" @click="doEdit(record)">编辑</a-button>
            <a-button 
              type="link" 
              color="purple" 
              v-if="record.priority < 99" 
              @click="doSetFeatured(record)"
            >
              精选
            </a-button>
            <a-popconfirm
              title="确定要删除吗？"
              ok-text="确定"
              cancel-text="取消"
              @confirm="doDelete(record.id)"
            >
              <a-button type="link" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { listAppVoByPageByAdmin, deleteAppByAdmin, updateApp } from '@/api/appController'

const router = useRouter()
const dataList = ref<API.AppVO[]>([])
const total = ref(0)
const loading = ref(false)

const searchParams = reactive<API.AppQueryRequest>({
  pageNum: 1,
  pageSize: 10,
  appName: '',
  userId: undefined,
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id' },
  { title: '应用名称', dataIndex: 'appName', key: 'appName' },
  { title: '封面', dataIndex: 'cover', key: 'cover' },
  { title: '创建人', dataIndex: 'user', key: 'user' },
  { title: '优先级', dataIndex: 'priority', key: 'priority' },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime' },
  { title: '操作', key: 'action' },
]

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await listAppVoByPageByAdmin(searchParams)
    if (res.data?.code === 0) {
      dataList.value = res.data.data.records || []
      pagination.total = Number(res.data.data.totalRow) || 0
    }
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
  searchParams.userId = undefined
  doSearch()
}

const handleTableChange = (pag: any) => {
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
  router.push(`/app/edit/${record.id}`)
}

const doSetFeatured = async (record: API.AppVO) => {
  const res = await updateApp({
    id: record.id,
    priority: 99
  })
  if (res.data?.code === 0) {
    message.success('设置精选成功')
    loadData()
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
#appAdminPage {
  padding: 24px;
  background: #fff;
  min-height: 100%;
}

.header {
  margin-bottom: 24px;
}

.search-form {
  margin-bottom: 24px;
  background: #fafafa;
  padding: 20px;
  border-radius: 8px;
}
</style>
