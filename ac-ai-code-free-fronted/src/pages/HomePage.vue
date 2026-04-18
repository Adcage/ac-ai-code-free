<template>
  <div id="homePage">
    <!-- 顶部搜索区 -->
    <div class="search-section">
      <h1 class="main-title">
        一句话 <span class="logo-text">呈所想</span>
      </h1>
      <p class="sub-title">与 AI 对话轻松创建应用和网站</p>

      <div class="search-container">
        <a-textarea
          v-model:value="searchText"
          placeholder="使用 NoCode 创建一个高效的小工具，帮我计算......"
          :auto-size="{ minRows: 4, maxRows: 6 }"
          class="main-input"
        />
        <div class="input-actions">
          <a-space>
            <a-button type="text" class="action-btn">
              <template #icon><paper-clip-outlined /></template>
              上传
            </a-button>
            <a-button type="text" class="action-btn" disabled>
              <template #icon><thunderbolt-outlined /></template>
              优化
            </a-button>
          </a-space>
          <a-button type="primary" shape="circle" class="send-btn" @click="doGenerate" :loading="loading">
            <template #icon><arrow-up-outlined /></template>
          </a-button>
        </div>
      </div>

      <div class="tag-suggestions">
        <a-button
          v-for="tag in suggestions"
          :key="tag"
          class="suggestion-tag"
          @click="searchText = tag"
        >
          {{ tag }}
        </a-button>
      </div>
    </div>

    <!-- 列表区：仅保留精选案例 -->
    <div class="content-section">
      <div class="list-container">
        <div class="list-header">
          <h2 class="section-title">精选案例</h2>
          <p class="section-desc">看看大家都在创作什么，寻找你的灵感</p>
        </div>
        <a-list
          :grid="{ gutter: 24, xs: 1, sm: 2, md: 3, lg: 3, xl: 3, xxl: 3 }"
          :data-source="goodAppList"
          :loading="goodLoading"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <AppCard 
                :app="item" 
                :showTime="false" 
                tagPosition="top-right"
                :coverHeight="180"
              >
                <template #tags>
                  <a-tag color="purple" v-if="item.priority >= 99">精选</a-tag>
                  <a-tag color="success" v-if="item.deployKey" size="small">已部署</a-tag>
                </template>
              </AppCard>
            </a-list-item>
          </template>
        </a-list>
        <div class="list-footer" v-if="goodTotal > goodAppList.length">
          <a-button @click="loadMoreGood" :loading="goodLoading">加载更多</a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { 
  PaperClipOutlined, 
  ThunderboltOutlined, 
  ArrowUpOutlined 
} from '@ant-design/icons-vue'
import { 
  addApp, 
  listGoodAppVoByPage 
} from '@/api/appController'
import AppCard from '@/components/AppCard.vue'

const router = useRouter()
const searchText = ref('')
const loading = ref(false)
const goodLoading = ref(false)

const suggestions = ['波普风电商页面', '企业网站', '电商运营后台', '暗黑话题社区']

const goodAppList = ref<API.AppVO[]>([])
const goodTotal = ref(0)

const goodSearchParams = ref<API.AppQueryRequest>({
  pageNum: 1,
  pageSize: 20,
})

/**
 * 加载精选案例
 */
const loadGoodApps = async (append = false) => {
  goodLoading.value = true
  try {
    const res = await listGoodAppVoByPage(goodSearchParams.value)
    const pageData = res.data?.data
    if (res.data?.code === 0 && pageData) {
      if (append) {
        goodAppList.value.push(...(pageData.records || []))
      } else {
        goodAppList.value = pageData.records || []
      }
      goodTotal.value = pageData.totalRow || 0
    }
  } finally {
    goodLoading.value = false
  }
}

const loadMoreGood = () => {
  goodSearchParams.value.pageNum = (goodSearchParams.value.pageNum ?? 1) + 1
  loadGoodApps(true)
}

/**
 * 生成应用
 */
const doGenerate = async () => {
  if (!searchText.value) {
    message.warning('请输入需求提示词')
    return
  }
  loading.value = true
  try {
    const res = await addApp({
      initPrompt: searchText.value,
      codeGenType: 'vue_project',
    })
    if (res.data?.code === 0) {
      router.push(`/app/generate/${res.data.data}`)
    } else {
      message.error('创建失败，' + res.data?.message)
    }
  } catch (e: any) {
    message.error('操作失败，' + e.message)
  } finally {
    loading.value = false
  }
}

const goToApp = (id: any) => {
  router.push(`/app/generate/${id}`)
}

onMounted(() => {
  loadGoodApps()
})
</script>

<style scoped>
/* 样式同之前，去掉了我的作品相关部分 */
#homePage {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0fdf4 0%, #eff6ff 50%, #fafafa 100%);
  padding-bottom: 60px;
}

.search-section {
  padding: 80px 20px 60px;
  text-align: center;
  max-width: 900px;
  margin: 0 auto;
}

.main-title {
  font-size: 48px;
  font-weight: 800;
  color: #1a1a1a;
  margin-bottom: 16px;
}

.logo-text {
  background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.sub-title {
  font-size: 18px;
  color: #666;
  margin-bottom: 40px;
}

.search-container {
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.05);
  padding: 16px;
  position: relative;
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.main-input {
  border: none !important;
  box-shadow: none !important;
  font-size: 16px;
  resize: none;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding: 0 8px;
}

.send-btn {
  width: 44px;
  height: 44px;
  background: #1a1a1a;
  border-color: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tag-suggestions {
  margin-top: 24px;
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.suggestion-tag {
  border-radius: 10px;
  border: none;
  background: rgba(255, 255, 255, 0.8);
  padding: 4px 16px;
  height: 36px;
}

.content-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.list-container {
  margin-bottom: 60px;
}

.section-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
}

.section-desc {
  color: #8c8c8c;
  margin-bottom: 24px;
}

.list-footer {
  text-align: center;
  margin-top: 24px;
}
</style>
