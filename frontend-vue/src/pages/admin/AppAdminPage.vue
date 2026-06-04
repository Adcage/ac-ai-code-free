<template>
  <div id="appAdminPage">
    <div class="page-header">
      <h2 class="page-title">应用管理</h2>
    </div>

    <div class="search-card">
      <a-form layout="inline" :model="searchParams" @finish="doSearch">
        <a-form-item label="应用名称">
          <a-input v-model:value="searchParams.appName" placeholder="请输入名称" allow-clear />
        </a-form-item>
        <a-form-item label="生成类型">
          <a-select
            v-model:value="searchParams.codeGenType"
            placeholder="请选择"
            style="width: 140px"
            allow-clear
          >
            <a-select-option value="ai">AI 生成</a-select-option>
            <a-select-option value="template">组件库</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="创建人">
          <a-input v-model:value="searchParams.userName" placeholder="请输入创建人名称" allow-clear />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit">查询</a-button>
            <a-button @click="resetSearch">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </div>

    <div class="table-card">
      <a-table
        :columns="columns"
        :data-source="dataList"
        :pagination="pagination"
        :loading="loading"
        size="middle"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'cover'">
            <a-image :src="record.cover" :width="50" :fallback="fallbackImage" style="border-radius: 4px" />
          </template>
          
          <template v-if="column.dataIndex === 'user'">
            <a-space v-if="record.user">
              <UserAvatar :user="record.user" size="small" />
              <span class="user-name">{{ record.user?.userName }}</span>
            </a-space>
            <span v-else class="text-secondary">未知用户</span>
          </template>

          <template v-if="column.dataIndex === 'codeGenType'">
            <a-tag :color="record.codeGenType === 'ai' ? 'green' : 'blue'">
              {{ record.codeGenType === 'ai' ? 'AI 生成' : '组件库' }}
            </a-tag>
          </template>

          <template v-if="column.dataIndex === 'priority'">
            <a-tag :color="record.priority >= 99 ? 'purple' : 'blue'">
              {{ record.priority }}
            </a-tag>
          </template>

          <template v-if="column.dataIndex === 'createTime'">
            <span class="time-text">{{ dayjs(record.createTime).format('YYYY-MM-DD HH:mm:ss') }}</span>
          </template>

          <template v-if="column.key === 'action'">
            <div class="action-slots">
              <div class="action-slot">
                <a-button type="link" size="small" @click="doEdit(record)">编辑</a-button>
              </div>
              <div class="action-slot">
                <a-button
                  v-if="record.priority < 99"
                  type="link"
                  size="small"
                  @click="doSetFeatured(record)"
                  style="color: #722ed1"
                >
                  精选
                </a-button>
              </div>
              <div class="action-slot">
                <a-popconfirm
                  title="确定要删除吗？"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="doDelete(record.id)"
                >
                  <a-button type="link" size="small" danger>删除</a-button>
                </a-popconfirm>
              </div>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 编辑模态框 -->
    <AppEditModal ref="editModalRef" @success="loadData" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { listAppVoByPageByAdmin, deleteAppByAdmin, updateApp } from '@/api/appController'
import dayjs from 'dayjs'
import UserAvatar from '@/components/UserAvatar.vue'
import AppEditModal from '@/components/AppEditModal.vue'

const dataList = ref<API.AppVO[]>([])
const loading = ref(false)
const editModalRef = ref()
const fallbackImage = 'https://gw.alipayobjects.com/zos/rmsportal/jZuoEvImRLnvkasqocpa.svg'

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
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 220, align: 'center' },
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
    const pageData = res.data?.data
    if (res.data?.code === 0 && pageData) {
      dataList.value = pageData.records || []
      pagination.total = Number(pageData.totalRow) || 0
    } else {
      message.error('加载失败，' + res.data?.message)
    }
  } catch (e: any) {
    message.error('加载失败，' + e.message)
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
  editModalRef.value?.open(record)
}

const doSetFeatured = async (record: API.AppVO) => {
  if (!record.id) {
    message.error('应用 ID 不存在，无法设置精选')
    return
  }
  const res = await updateApp({
    id: String(record.id),
    priority: 99,
  })
  if (res.data?.code === 0) {
    message.success('设置精选成功')
    loadData()
  } else {
    message.error('设置失败，' + res.data?.message)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
#appAdminPage {
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

.user-name {
  color: rgba(0, 0, 0, 0.65);
}

.time-text {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}

.text-secondary {
  color: rgba(0, 0, 0, 0.45);
}

.action-slots {
  display: flex;
  justify-content: center;
  align-items: center;
}

.action-slot {
  width: 60px; /* 固定槽位宽度 */
  display: flex;
  justify-content: center;
}

:deep(.ant-table-thead > tr > th) {
  background-color: #fafafa;
  font-weight: 500;
}
</style>
