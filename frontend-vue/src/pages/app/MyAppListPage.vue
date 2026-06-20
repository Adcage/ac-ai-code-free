<template>
  <div class="my-app-page">
    <div class="page-container">
      <div class="page-header">
        <div class="header-left">
          <h1 class="page-title">我的作品</h1>
          <p class="page-desc">管理你的所有 AI 创作项目</p>
        </div>
        <a-button type="primary" class="create-btn" @click="goToCreate">
          <template #icon><Plus :size="16" /></template>
          创建新应用
        </a-button>
      </div>

      <div v-if="loading && dataList.length === 0" class="loading-state">
        <a-spin size="large" />
      </div>

      <div v-else-if="dataList.length === 0" class="empty-state">
        <div class="empty-icon"><FolderOpen :size="64" /></div>
        <h3 class="empty-title">还没有作品</h3>
        <p class="empty-desc">开始创作吧，AI 帮你把想法变成现实</p>
        <a-button type="primary" class="create-btn" @click="goToCreate">
          <template #icon><Plus :size="16" /></template>
          创建新应用
        </a-button>
      </div>

      <template v-else>
        <div class="app-grid">
          <AppCard
            v-for="item in dataList"
            :key="item.id"
            :app="item"
            :actions="['view', 'chat', 'edit', 'delete']"
            @delete="handleDeleteApp"
            @edit="handleEditApp"
          />
        </div>

        <div class="list-footer" v-if="loadingMore">
          <a-spin size="small" /> 加载中...
        </div>
        <div v-if="hasMore && !loadingMore" class="scroll-sentinel"></div>
      </template>
    </div>

    <AppEditModal ref="editModalRef" @success="loadData" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { Plus, FolderOpen } from '@lucide/vue'
import { listMyAppVoByPage, deleteApp } from '@/api/appController'
import AppCard from '@/components/AppCard.vue'
import AppEditModal from '@/components/AppEditModal.vue'

const router = useRouter()
const loading = ref(false)
const loadingMore = ref(false)
const dataList = ref<API.AppVO[]>([])
const total = ref(0)
const editModalRef = ref()

const hasMore = computed(() => dataList.value.length < total.value)

const searchParams = ref<API.AppQueryRequest>({
  pageNum: 1,
  pageSize: 20,
})

const loadData = async (append = false) => {
  if (append) {
    loadingMore.value = true
  } else {
    loading.value = true
  }
  try {
    const res = await listMyAppVoByPage(searchParams.value)
    const pageData = res.data?.data
    if (res.data?.code === 0 && pageData) {
      if (append) {
        dataList.value.push(...(pageData.records || []))
      } else {
        dataList.value = pageData.records || []
      }
      total.value = pageData.totalRow || 0
    }
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  if (loadingMore.value || !hasMore.value) return
  searchParams.value.pageNum = (searchParams.value.pageNum ?? 1) + 1
  loadData(true).then(() => observeSentinel())
}

let listObserver: IntersectionObserver | null = null

const setupObserver = () => {
  listObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && hasMore.value && !loadingMore.value) {
        loadMore()
      }
    },
    { rootMargin: '200px' },
  )
}

const observeSentinel = () => {
  if (!listObserver) setupObserver()
  nextTick(() => {
    const sentinel = document.querySelector('.scroll-sentinel')
    if (sentinel) listObserver!.observe(sentinel)
  })
}

const goToCreate = () => {
  router.push('/')
}

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
  } catch {
    message.error('删除失败，请稍后重试')
  } finally {
    hide()
  }
}

const handleEditApp = (app: API.AppVO) => {
  editModalRef.value?.open(app)
}

onMounted(() => {
  loadData().then(() => observeSentinel())
})

onUnmounted(() => {
  listObserver?.disconnect()
})
</script>

<style scoped>
.my-app-page {
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

.app-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.list-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: var(--space-2xl);
  color: var(--color-text-tertiary);
}

.scroll-sentinel {
  height: 1px;
}

@media (max-width: 1024px) {
  .app-grid {
    grid-template-columns: repeat(2, 1fr);
  }
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

  .app-grid {
    grid-template-columns: 1fr;
  }

  .page-title {
    font-size: 24px;
  }
}
</style>
