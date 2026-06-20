<template>
  <div class="usage-page">
    <div class="usage-container">
      <h1 class="page-title">用量统计</h1>

      <div v-if="loading" class="loading-state">
        <Loader2 :size="32" class="spin" />
        <span>加载中...</span>
      </div>

      <template v-else>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon-wrap">
              <Coins :size="22" />
            </div>
            <div class="stat-number">{{ formatNumber(stats.totalTokens) }}</div>
            <div class="stat-label">tokens</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon-wrap">
              <MessageSquare :size="22" />
            </div>
            <div class="stat-number">{{ formatNumber(stats.totalMessages) }}</div>
            <div class="stat-label">条消息</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon-wrap">
              <AppWindow :size="22" />
            </div>
            <div class="stat-number">{{ formatNumber(stats.totalApps) }}</div>
            <div class="stat-label">个应用</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon-wrap">
              <Clock :size="22" />
            </div>
            <div class="stat-number">{{ formatNumber(Math.round(stats.avgLatencyMs || 0)) }}</div>
            <div class="stat-label">ms 平均响应</div>
          </div>
        </div>

        <div class="chart-card">
          <h2 class="section-title">近 7 天用量趋势</h2>
          <div v-if="stats.recentDailyUsage && stats.recentDailyUsage.length > 0" class="bar-chart">
            <div v-for="(day, index) in stats.recentDailyUsage" :key="index" class="bar-item">
              <div class="bar-value">{{ formatNumber((day.inputTokens || 0) + (day.outputTokens || 0)) }}</div>
              <div class="bar-wrapper">
                <div class="bar-fill" :style="{ height: getBarHeight(day) + '%' }"></div>
              </div>
              <div class="bar-label">{{ formatDateShort(day.date || '') }}</div>
            </div>
          </div>
          <div v-else class="empty-chart">
            <BarChart3 :size="40" />
            <p>暂无用量数据</p>
          </div>
        </div>

        <div class="recent-card">
          <h2 class="section-title">最近对话</h2>
          <div v-if="recentChats.length > 0" class="chat-list">
            <div v-for="chat in recentChats" :key="chat.id" class="chat-item">
              <div class="chat-info">
                <div class="chat-app">{{ chat.appName || '未命名应用' }}</div>
                <div class="chat-time">{{ formatDateTime(chat.createTime || '') }}</div>
              </div>
              <div class="chat-tokens">
                {{ formatNumber((chat.inputTokens || 0) + (chat.outputTokens || 0)) }} tokens
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <MessageSquare :size="40" />
            <p>暂无对话记录</p>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/request'
import { Coins, MessageSquare, AppWindow, Clock, BarChart3, Loader2 } from '@lucide/vue'

interface DailyUsage {
  date?: string
  inputTokens?: number
  outputTokens?: number
  messages?: number
}

interface UsageStats {
  totalInputTokens: number
  totalOutputTokens: number
  totalTokens: number
  totalMessages: number
  totalApps: number
  totalSessions: number
  avgLatencyMs: number
  recentDailyUsage: DailyUsage[]
}

interface ChatRecord {
  id: number
  appName?: string
  createTime?: string
  inputTokens?: number
  outputTokens?: number
}

const loading = ref(true)
const stats = ref<UsageStats>({
  totalInputTokens: 0,
  totalOutputTokens: 0,
  totalTokens: 0,
  totalMessages: 0,
  totalApps: 0,
  totalSessions: 0,
  avgLatencyMs: 0,
  recentDailyUsage: [],
})
const recentChats = ref<ChatRecord[]>([])

onMounted(async () => {
  try {
    const res = await request.get('/user/usage/stats')
    if (res.data.code === 0 && res.data.data) {
      const data = res.data.data
      stats.value = {
        totalInputTokens: data.totalInputTokens || 0,
        totalOutputTokens: data.totalOutputTokens || 0,
        totalTokens: (data.totalInputTokens || 0) + (data.totalOutputTokens || 0),
        totalMessages: data.totalMessages || 0,
        totalApps: data.totalApps || 0,
        totalSessions: data.totalSessions || 0,
        avgLatencyMs: data.avgLatencyMs || 0,
        recentDailyUsage: data.recentDailyUsage || [],
      }
      if (data.recentDailyUsage) {
        recentChats.value = data.recentDailyUsage
          .filter((d: DailyUsage) => (d.messages ?? 0) > 0)
          .map((d: DailyUsage, i: number) => ({
            id: i,
            appName: '对话记录',
            createTime: d.date,
            inputTokens: d.inputTokens,
            outputTokens: d.outputTokens,
          }))
      }
    }
  } catch {
    message.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
})

const getBarHeight = (day: DailyUsage) => {
  const maxTokens = Math.max(
    ...stats.value.recentDailyUsage.map((d) => (d.inputTokens || 0) + (d.outputTokens || 0)),
    1,
  )
  const tokens = (day.inputTokens || 0) + (day.outputTokens || 0)
  return Math.max((tokens / maxTokens) * 100, 2)
}

const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return String(num)
}

const formatDateShort = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.usage-page {
  min-height: calc(100vh - 64px);
  background: var(--color-background);
  padding: var(--space-2xl) var(--space-md);
}

.usage-container {
  max-width: 1000px;
  margin: 0 auto;
}

.page-title {
  font-family: var(--font-heading);
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-xl);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-3xl);
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.stat-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
  border: 1px solid var(--color-border);
  text-align: center;
  transition: all var(--transition-normal);
}

.stat-card:hover {
  border-color: var(--color-border-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: rgba(34, 197, 94, 0.1);
  color: var(--color-cta);
  margin-bottom: var(--space-md);
}

.stat-number {
  font-family: var(--font-heading);
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1;
  margin-bottom: var(--space-xs);
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-muted);
}

.chart-card,
.recent-card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  border: 1px solid var(--color-border);
  margin-bottom: var(--space-lg);
}

.section-title {
  font-family: var(--font-heading);
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: var(--space-lg);
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 200px;
  padding: var(--space-md) 0;
  gap: var(--space-sm);
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
  justify-content: flex-end;
}

.bar-value {
  font-family: var(--font-heading);
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
  white-space: nowrap;
}

.bar-wrapper {
  width: 100%;
  max-width: 48px;
  flex: 1;
  display: flex;
  align-items: flex-end;
}

.bar-fill {
  width: 100%;
  background: linear-gradient(180deg, var(--color-cta) 0%, rgba(34, 197, 94, 0.5) 100%);
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  transition: height 0.5s ease;
  min-height: 4px;
}

.bar-label {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: var(--space-sm);
}

.empty-chart,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-2xl);
  color: var(--color-text-muted);
}

.chat-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.chat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.chat-item:hover {
  background: var(--color-surface-elevated);
}

.chat-app {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
}

.chat-time {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

.chat-tokens {
  font-family: var(--font-heading);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-cta);
  white-space: nowrap;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-number {
    font-size: 24px;
  }

  .bar-chart {
    height: 160px;
  }
}

@media (max-width: 375px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
