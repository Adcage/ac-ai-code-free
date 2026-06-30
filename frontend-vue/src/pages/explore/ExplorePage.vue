<template>
  <div class="explore-page">
    <div class="explore-container">
      <!-- 页面标题块：橙竖线 + 标题 -->
      <div class="page-title-block">
        <div class="accent-bar"></div>
        <div>
          <h1 class="page-title">探索广场</h1>
          <p class="page-subtitle">发现社区创建的精彩应用</p>
        </div>
      </div>

      <!-- 筛选栏：纯文字按钮 + 底部橙线 -->
      <div class="filter-bar">
        <div class="filter-cats">
          <button
            v-for="cat in categories"
            :key="cat"
            :class="['filter-btn', { active: selectedCategory === cat }]"
            @click="selectCategory(cat)"
          >
            {{ cat }}
          </button>
        </div>
        <div class="filter-sort">
          <button :class="['filter-btn', { active: sortOrder === 'latest' }]" @click="selectSort('latest')">
            最新
          </button>
          <button :class="['filter-btn', { active: sortOrder === 'popular' }]" @click="selectSort('popular')">
            最热
          </button>
        </div>
      </div>

      <div v-if="loading && dataList.length === 0" class="loading-state">
        <Loader2 :size="32" class="spin" />
        <span>加载中...</span>
      </div>

      <template v-else-if="dataList.length > 0">
        <!-- 4 列卡片网格：无边框卡片 -->
        <div class="app-grid">
          <div v-for="app in dataList" :key="app.id" class="app-card">
            <div class="card-cover">
              <img v-if="app.cover" :src="app.cover" :alt="app.appName" />
              <span v-else class="cover-initial">{{ (app.appName || '?')[0] }}</span>
            </div>
            <div class="card-body">
              <h3 class="card-name">{{ app.appName || '未命名应用' }}</h3>
              <div class="card-author">
                <span class="author-dot"></span>
                <span>{{ app.user?.userName || '匿名' }}</span>
              </div>
              <div class="card-tags" v-if="app.categories?.length">
                {{ app.categories.join(' / ') }}
              </div>
              <div class="card-footer">
                <span class="card-forks">{{ app.forkCount || 0 }} forks</span>
                <button class="btn-fork" @click="handleFork(app.id!)">Fork</button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="loading && dataList.length > 0" class="loading-more">
          <Loader2 :size="20" class="spin" />
        </div>

        <div v-if="dataList.length < total" class="sentinel">— 滚动加载更多 —</div>
      </template>

      <div v-else class="empty-state">
        <Compass :size="48" />
        <p>暂无公开应用</p>
      </div>

      <div ref="sentinelRef" class="scroll-sentinel"></div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import request from '@/request'
import { Compass, Loader2 } from '@lucide/vue'

const router = useRouter()

const categories = ['全部', '工具', '游戏', '社交', '教育', '商业', '创意']
const selectedCategory = ref('全部')
const sortOrder = ref<'latest' | 'popular'>('latest')
const loading = ref(false)
const dataList = ref<any[]>([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = 20

const sentinelRef = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

const loadData = async (append = false) => {
  if (loading.value) return
  loading.value = true
  try {
    const params: any = {
      pageNum: pageNum.value,
      pageSize,
      sortField: sortOrder.value,
    }
    if (selectedCategory.value !== '全部') {
      params.category = selectedCategory.value
    }
    const res = await request.post('/app/marketplace/list/page/vo', params)
    if (res.data.code === 0 && res.data.data) {
      const records = res.data.data.records || []
      if (append) {
        dataList.value.push(...records)
      } else {
        dataList.value = records
      }
      total.value = res.data.data.totalRow || 0
    }
  } catch {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const selectCategory = (cat: string) => {
  selectedCategory.value = cat
  pageNum.value = 1
  dataList.value = []
  loadData(false)
}

const selectSort = (sort: 'latest' | 'popular') => {
  sortOrder.value = sort
  pageNum.value = 1
  dataList.value = []
  loadData(false)
}

const handleFork = async (appId: number) => {
  try {
    const res = await request.post('/app/fork', { appId })
    if (res.data.code === 0 && res.data.data) {
      message.success('Fork 成功！正在跳转...')
      router.push(`/app/generate/${res.data.data}`)
    } else {
      message.error(res.data.message || 'Fork 失败')
    }
  } catch {
    message.error('Fork 失败')
  }
}

const handleIntersect = (entries: IntersectionObserverEntry[]) => {
  if (entries[0].isIntersecting && !loading.value && dataList.value.length < total.value) {
    pageNum.value++
    loadData(true)
  }
}

onMounted(() => {
  loadData()
  observer = new IntersectionObserver(handleIntersect, { threshold: 0.1 })
  if (sentinelRef.value) observer.observe(sentinelRef.value)
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>

<style scoped>
.explore-page {
  min-height: calc(100vh - 64px);
  background: var(--color-background);
}

.explore-container {
  max-width: var(--container-widescreen);
  margin: 0 auto;
  padding: 0 var(--space-page-x);
}

/* ── 页面标题块：橙竖线 + 标题 ── */
.page-title-block {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: var(--space-block);
  padding-top: var(--space-section);
}

.accent-bar {
  width: var(--accent-bar-width);
  height: var(--accent-bar-height);
  background: var(--color-cta);
  flex-shrink: 0;
  margin-top: 8px;
}

.page-title {
  font-family: var(--font-heading);
  font-size: var(--size-page-title);
  font-weight: 700;
  letter-spacing: -1px;
  line-height: 1.1;
  color: var(--color-text);
}

.page-subtitle {
  font-size: 16px;
  color: var(--color-text-secondary);
  margin-top: 8px;
}

/* ── 筛选栏：底部 1px 分隔线 ── */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 40px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.filter-cats,
.filter-sort {
  display: flex;
  gap: 24px;
}

.filter-btn {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  background: none;
  border: none;
  padding: 0 0 4px;
  cursor: pointer;
  position: relative;
  transition: color var(--transition-fast);
}

.filter-btn.active {
  color: var(--color-text);
  font-weight: 600;
}

.filter-btn.active::after {
  content: '';
  position: absolute;
  bottom: -16px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--color-cta);
}

.filter-btn:hover:not(.active) {
  color: var(--color-text);
}

/* ── 4 列卡片网格：无边框无阴影 ── */
.app-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-xl);
}

.app-card {
  cursor: pointer;
  transition: transform var(--transition-fast);
}

.app-card:hover {
  transform: translateY(-2px);
}

.app-card:hover .card-cover {
  background: linear-gradient(135deg, #e8ddd4 0%, #dcd0c5 100%);
}

.card-cover {
  height: 160px;
  background: linear-gradient(135deg, var(--color-surface-alt) 0%, #e8ddd4 100%);
  transition: background 0.3s;
  margin-bottom: 16px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-initial {
  font-family: var(--font-heading);
  font-size: 96px;
  font-weight: 700;
  color: var(--color-text);
  opacity: 0.05;
  user-select: none;
  line-height: 1;
}

.card-body {
  /* 无 padding，内容直接对齐网格 */
}

.card-name {
  font-family: var(--font-heading);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
  color: var(--color-text);
}

.card-author {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.author-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-cta);
  flex-shrink: 0;
}

.card-tags {
  font-size: 12px;
  color: var(--color-cta);
  margin-bottom: 12px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.card-forks {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.btn-fork {
  padding: 4px 16px;
  border: 1px solid var(--color-cta);
  color: var(--color-cta);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  background: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  border-radius: 0;
}

.btn-fork:hover {
  background: var(--color-cta);
  color: #fff;
}

/* ── 状态 ── */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-section);
  color: var(--color-text-muted);
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading-more {
  display: flex;
  justify-content: center;
  padding: var(--space-lg);
  color: var(--color-text-muted);
}

.sentinel {
  text-align: center;
  padding: var(--space-block) 0;
  color: var(--color-text-muted);
  font-size: 14px;
}

.scroll-sentinel {
  height: 1px;
}

/* ── 响应式 ── */
@media (max-width: 1024px) {
  .app-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .explore-container {
    padding: 0 var(--space-page-x-sm);
  }

  .app-grid {
    grid-template-columns: 1fr;
  }

  .page-title {
    font-size: 32px;
  }

  .page-title-block {
    padding-top: var(--space-section-tight);
  }

  .filter-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .filter-sort {
    margin-top: 4px;
  }
}
</style>
