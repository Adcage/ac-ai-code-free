<template>
  <div id="myAppListPage" class="container-page">
    <div class="header-section">
      <h2 class="page-title">我的作品</h2>
      <p class="page-desc">这里记录了你所有的 AI 创作结晶</p>
    </div>

    <a-list
      :grid="{ gutter: 24, xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 4 }"
      :data-source="dataList"
      :loading="loading"
      class="app-list"
    >
      <template #renderItem="{ item }">
        <a-list-item>
          <AppCard 
            :app="item" 
            :actions="['view', 'chat', 'edit', 'delete']"
            @delete="handleDeleteApp"
            @edit="handleEditApp"
          />
        </a-list-item>
      </template>
    </a-list>

    <!-- 编辑模态框 -->
    <AppEditModal ref="editModalRef" @success="loadData" />

    <div class="list-footer" v-if="total > dataList.length">
      <a-button @click="loadMore" :loading="loading">加载更多</a-button>
    </div>

    <a-empty v-if="!loading && dataList.length === 0" description="暂无作品，快去主页创作一个吧" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { listMyAppVoByPage, deleteApp } from '@/api/appController'
import AppCard from '@/components/AppCard.vue'
import AppEditModal from '@/components/AppEditModal.vue'

const loading = ref(false)
const dataList = ref<API.AppVO[]>([])
const total = ref(0)
const editModalRef = ref()

const searchParams = ref<API.AppQueryRequest>({
  pageNum: 1,
  pageSize: 20,
})

const loadData = async (append = false) => {
  loading.value = true
  try {
    const res = await listMyAppVoByPage(searchParams.value)
    if (res.data?.code === 0) {
      if (append) {
        dataList.value.push(...(res.data.data.records || []))
      } else {
        dataList.value = res.data.data.records || []
      }
      total.value = res.data.data.totalRow || 0
    }
  } finally {
    loading.value = false
  }
}

const loadMore = () => {
  searchParams.value.pageNum++
  loadData(true)
}

/**
 * 处理删除应用
 */
const handleDeleteApp = async (id: number) => {
  if (!id) return
  const hide = message.loading('正在删除...', 0)
  try {
    const res = await deleteApp({ id })
    if (res.data?.code === 0) {
      message.success('删除成功')
      loadData()
    } else {
      message.error('删除失败，' + res.data?.message)
    }
  } catch (error) {
    message.error('删除失败，请稍后重试')
  } finally {
    hide()
  }
}

/**
 * 处理编辑应用
 */
const handleEditApp = (app: API.AppVO) => {
  editModalRef.value?.open(app)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.container-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  min-height: calc(100vh - 64px);
}

.header-section {
  margin-bottom: 40px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.page-desc {
  color: #8c8c8c;
  font-size: 16px;
}

.list-footer {
  text-align: center;
  margin-top: 40px;
}
</style>
