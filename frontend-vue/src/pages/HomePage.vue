<template>
  <div id="homePage">
    <section class="hero-section">
      <div class="hero-bg-glow"></div>
      <div class="hero-content">
        <h1 class="hero-title">一句话，让 <span class="text-cta">AI</span> 为你写代码</h1>
        <p class="hero-subtitle">与 AI 对话，轻松创建应用和网站</p>

        <div class="search-container">
          <a-textarea
            v-model:value="searchText"
            placeholder="描述你想要的应用，例如：帮我创建一个极简风格的个人博客..."
            :auto-size="{ minRows: 3, maxRows: 6 }"
            class="search-textarea"
          />
          <div class="search-actions">
            <div class="search-actions-left">
              <a-tooltip title="在生成器中上传参考文件">
                <a-button type="text" class="action-btn" @click="goToGenerate">
                  <template #icon><Paperclip :size="16" /></template>
                  上传
                </a-button>
              </a-tooltip>
              <a-tooltip title="AI 帮你优化提示词，生成更精准的代码">
                <a-button
                  type="text"
                  class="action-btn"
                  :disabled="!searchText.trim()"
                  :loading="enhancing"
                  @click="doEnhance"
                >
                  <template #icon><Sparkles :size="16" /></template>
                  优化
                </a-button>
              </a-tooltip>
            </div>
            <a-button type="primary" shape="circle" class="send-btn" @click="doGenerate" :loading="loading">
              <template #icon><ArrowUp :size="20" /></template>
            </a-button>
          </div>
        </div>

        <div class="style-templates">
          <div
            v-for="tpl in styleTemplates"
            :key="tpl.value"
            :class="['style-tag', { 'style-tag-active': selectedStyle === tpl.value }]"
            @click="selectedStyle = tpl.value"
          >
            {{ tpl.label }}
          </div>
        </div>

        <div class="tag-suggestions">
          <span v-for="tag in suggestions" :key="tag" class="suggestion-chip" @click="searchText = tag">
            {{ tag }}
          </span>
        </div>
      </div>
    </section>

    <section class="features-section">
      <div class="section-inner">
        <h2 class="section-heading">为什么选择 AC AI Code</h2>
        <p class="section-subheading">强大的 AI 驱动，让创意变为现实</p>

        <div class="bento-grid">
          <div class="bento-card bento-span-2">
            <div class="bento-icon"><Sparkles :size="28" /></div>
            <h3 class="bento-title">AI 智能生成</h3>
            <p class="bento-desc">与 AI 对话，一句话描述需求即可生成完整应用代码</p>
          </div>
          <div class="bento-card">
            <div class="bento-icon"><Layers :size="28" /></div>
            <h3 class="bento-title">多模式支持</h3>
            <p class="bento-desc">支持单文件、多文件、Vue 工程三种生成模式，灵活适配不同场景</p>
          </div>
          <div class="bento-card">
            <div class="bento-icon"><Eye :size="28" /></div>
            <h3 class="bento-title">实时预览</h3>
            <p class="bento-desc">生成过程中实时预览效果，边看边调</p>
          </div>
          <div class="bento-card bento-span-2">
            <div class="bento-icon"><Palette :size="28" /></div>
            <h3 class="bento-title">风格模板</h3>
            <p class="bento-desc">内置极简、商务、科技等多种风格模板，一键切换</p>
          </div>
          <div class="bento-card">
            <div class="bento-icon"><Rocket :size="28" /></div>
            <h3 class="bento-title">一键部署</h3>
            <p class="bento-desc">代码生成后一键部署上线，即刻分享</p>
          </div>
          <div class="bento-card bento-span-full">
            <div class="bento-icon"><GitBranch :size="28" /></div>
            <h3 class="bento-title">版本管理</h3>
            <p class="bento-desc">每次修改自动记录版本，随时回退到任意历史版本</p>
          </div>
        </div>
      </div>
    </section>

    <section class="steps-section">
      <div class="section-inner">
        <h2 class="section-heading">三步创建你的应用</h2>

        <div class="steps-row">
          <div class="step-item">
            <div class="step-number">1</div>
            <div class="step-icon"><MessageSquare :size="24" /></div>
            <h3 class="step-title">描述需求</h3>
            <p class="step-desc">输入你想要的应用描述，选择喜欢的风格模板</p>
          </div>

          <div class="step-arrow"><ChevronRight :size="24" /></div>

          <div class="step-item">
            <div class="step-number">2</div>
            <div class="step-icon"><Cpu :size="24" /></div>
            <h3 class="step-title">AI 生成</h3>
            <p class="step-desc">AI 智能理解需求，自动生成完整代码</p>
          </div>

          <div class="step-arrow"><ChevronRight :size="24" /></div>

          <div class="step-item">
            <div class="step-number">3</div>
            <div class="step-icon"><Globe :size="24" /></div>
            <h3 class="step-title">预览部署</h3>
            <p class="step-desc">实时预览效果，一键部署上线</p>
          </div>
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <div class="section-inner">
        <h2 class="section-heading">精选案例</h2>
        <p class="section-subheading">看看大家都在创作什么</p>

        <div class="showcase-grid" v-if="goodAppList.length > 0">
          <AppCard
            v-for="item in goodAppList"
            :key="item.id"
            :app="item"
            :showTime="false"
            tagPosition="top-right"
            :coverHeight="180"
          >
            <template #tags>
              <a-tag color="purple" v-if="(item.priority ?? 0) >= 99">精选</a-tag>
              <a-tag color="success" v-if="item.deployKey" size="small">已部署</a-tag>
            </template>
          </AppCard>
        </div>

        <div class="showcase-empty" v-else-if="!goodLoading">
          <Eye :size="32" />
          <p>暂无精选案例，快来创建第一个作品吧</p>
        </div>

        <div class="showcase-footer" v-if="goodTotal > goodAppList.length">
          <a-button class="load-more-btn" @click="loadMoreGood" :loading="goodLoading"> 加载更多 </a-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  Paperclip,
  Sparkles,
  ArrowUp,
  Layers,
  Eye,
  Palette,
  Rocket,
  GitBranch,
  MessageSquare,
  Cpu,
  Globe,
  ChevronRight,
} from '@lucide/vue'
import { addApp, listGoodAppVoByPage, enhancePrompt } from '@/api/appController'
import AppCard from '@/components/AppCard.vue'

const router = useRouter()
const searchText = ref('')
const loading = ref(false)
const enhancing = ref(false)
const goodLoading = ref(false)
const selectedStyle = ref('')

const styleTemplates = [
  { label: '极简', value: 'minimal' },
  { label: '商务', value: 'business' },
  { label: '科技', value: 'tech' },
  { label: '活泼', value: 'playful' },
  { label: '暗黑', value: 'dark' },
]

const suggestions = ['波普风电商页面', '企业官网', '电商运营后台', '暗黑话题社区']

const goodAppList = ref<API.AppVO[]>([])
const goodTotal = ref(0)

const goodSearchParams = ref<API.AppQueryRequest>({
  pageNum: 1,
  pageSize: 20,
})

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

const doGenerate = async () => {
  if (!searchText.value) {
    message.warning('请输入需求提示词')
    return
  }
  loading.value = true
  try {
    const res = await addApp({
      initPrompt: searchText.value,
      styleTemplate: selectedStyle.value || undefined,
    })
    if (res.data?.code === 0) {
      router.push(`/app/generate/${res.data.data}`)
    } else {
      message.error('创建失败，' + res.data?.message)
    }
  } catch (e: unknown) {
    message.error('操作失败，' + (e instanceof Error ? e.message : String(e)))
  } finally {
    loading.value = false
  }
}

const doEnhance = async () => {
  const prompt = searchText.value.trim()
  if (!prompt) {
    message.warning('请先输入需求描述')
    return
  }
  enhancing.value = true
  try {
    const res = await enhancePrompt({ prompt })
    if (res.data?.code === 0 && res.data?.data) {
      searchText.value = res.data.data
      message.success('提示词优化完成')
    } else {
      message.error('优化失败，' + (res.data?.message ?? '未知错误'))
    }
  } catch (e: unknown) {
    message.error('优化失败，' + (e instanceof Error ? e.message : String(e)))
  } finally {
    enhancing.value = false
  }
}

const goToGenerate = () => {
  if (searchText.value.trim()) {
    doGenerate()
  } else {
    message.info('请先输入需求描述，或直接在生成器页面操作')
  }
}

onMounted(() => {
  loadGoodApps()
})
</script>

<style scoped>
#homePage {
  min-height: 100vh;
  background: var(--color-background);
}

.hero-section {
  position: relative;
  min-height: 80vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-3xl) var(--space-lg);
  overflow: hidden;
}

.hero-bg-glow {
  position: absolute;
  top: -20%;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(34, 197, 94, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 800px;
  width: 100%;
  text-align: center;
}

.hero-title {
  font-family: var(--font-heading);
  font-size: 52px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1.2;
  margin-bottom: var(--space-md);
}

.text-cta {
  color: var(--color-cta);
}

.hero-subtitle {
  font-size: 20px;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2xl);
}

.search-container {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-md);
  backdrop-filter: blur(12px);
}

.search-textarea {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--color-text) !important;
  font-size: 16px;
  resize: none;
  padding: var(--space-sm) var(--space-sm);
}

.search-textarea::placeholder {
  color: var(--color-text-muted);
}

.search-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-sm);
  padding: 0 var(--space-sm);
}

.search-actions-left {
  display: flex;
  gap: var(--space-xs);
}

.action-btn {
  color: var(--color-text-muted) !important;
  font-size: 14px;
}

.action-btn:hover:not(:disabled) {
  color: var(--color-text-secondary) !important;
}

.send-btn {
  width: 44px;
  height: 44px;
  background: var(--color-cta) !important;
  border-color: var(--color-cta) !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover {
  background: var(--color-cta-hover) !important;
  border-color: var(--color-cta-hover) !important;
}

.style-templates {
  display: flex;
  justify-content: center;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
  flex-wrap: wrap;
}

.style-tag {
  padding: 6px 20px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--transition-normal);
  user-select: none;
}

.style-tag:hover {
  border-color: var(--color-border-light);
  color: var(--color-text-secondary);
}

.style-tag-active {
  border-color: var(--color-cta);
  color: var(--color-cta);
  background: rgba(34, 197, 94, 0.08);
}

.tag-suggestions {
  display: flex;
  justify-content: center;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  flex-wrap: wrap;
}

.suggestion-chip {
  padding: 6px 16px;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-normal);
  border: 1px solid transparent;
}

.suggestion-chip:hover {
  background: var(--color-surface-elevated);
  border-color: var(--color-border);
  color: var(--color-text);
}

.features-section,
.steps-section,
.showcase-section {
  padding: var(--space-3xl) var(--space-lg);
}

.section-inner {
  max-width: 1200px;
  margin: 0 auto;
}

.section-heading {
  font-family: var(--font-heading);
  font-size: 36px;
  font-weight: 700;
  color: var(--color-text);
  text-align: center;
  margin-bottom: var(--space-sm);
}

.section-subheading {
  font-size: 18px;
  color: var(--color-text-secondary);
  text-align: center;
  margin-bottom: var(--space-2xl);
}

.bento-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
}

.bento-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  transition: all var(--transition-normal);
  cursor: default;
}

.bento-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-border-light);
}

.bento-span-2 {
  grid-column: span 2;
}

.bento-span-full {
  grid-column: span 3;
}

.bento-icon {
  color: var(--color-cta);
  margin-bottom: var(--space-md);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: rgba(34, 197, 94, 0.1);
  border-radius: var(--radius-md);
}

.bento-title {
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-sm);
}

.bento-desc {
  font-size: 15px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.steps-row {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: var(--space-md);
  margin-top: var(--space-2xl);
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  flex: 1;
  max-width: 280px;
}

.step-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-cta);
  color: #fff;
  font-family: var(--font-heading);
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-md);
}

.step-icon {
  color: var(--color-cta);
  margin-bottom: var(--space-md);
}

.step-title {
  font-family: var(--font-heading);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-sm);
}

.step-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.step-arrow {
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  padding-top: 60px;
}

.showcase-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
}

.showcase-footer {
  text-align: center;
  margin-top: var(--space-xl);
}

.load-more-btn {
  background: var(--color-surface) !important;
  border-color: var(--color-border) !important;
  color: var(--color-text-secondary) !important;
  transition: all var(--transition-normal);
}

.load-more-btn:hover {
  border-color: var(--color-cta) !important;
  color: var(--color-cta) !important;
}

@media (max-width: 1024px) {
  .hero-title {
    font-size: 40px;
  }

  .bento-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .bento-span-2 {
    grid-column: span 2;
  }

  .bento-span-full {
    grid-column: span 2;
  }

  .showcase-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hero-section {
    min-height: auto;
    padding: var(--space-2xl) var(--space-md);
  }

  .hero-title {
    font-size: 32px;
  }

  .hero-subtitle {
    font-size: 16px;
  }

  .bento-grid {
    grid-template-columns: 1fr;
  }

  .bento-span-2,
  .bento-span-full {
    grid-column: span 1;
  }

  .steps-row {
    flex-direction: column;
    align-items: center;
  }

  .step-arrow {
    transform: rotate(90deg);
    padding-top: 0;
    padding: var(--space-sm) 0;
  }

  .showcase-grid {
    grid-template-columns: 1fr;
  }

  .section-heading {
    font-size: 28px;
  }

  .features-section,
  .steps-section,
  .showcase-section {
    padding: var(--space-2xl) var(--space-md);
  }
}

@media (max-width: 375px) {
  .hero-title {
    font-size: 26px;
  }

  .style-templates {
    gap: var(--space-xs);
  }

  .style-tag {
    padding: 4px 12px;
    font-size: 13px;
  }
}
</style>
