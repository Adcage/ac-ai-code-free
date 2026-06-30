<template>
  <div class="dashboard-page">
    <div class="dashboard-container">
      <!-- 深色区域：背景全宽，内容约束在 1440px 容器内 -->
      <div class="dark-section">
        <div class="dark-section-inner">
          <div class="page-title-block">
            <div class="accent-bar"></div>
            <div>
              <h1 class="page-title">Token 用量</h1>
              <p class="page-subtitle">追踪你的 AI 消耗与运行情况</p>
            </div>
            <div class="time-toggle-wrap">
              <a-radio-group v-model:value="days" button-style="solid" size="small" @change="loadData">
                <a-radio-button :value="7">7 天</a-radio-button>
                <a-radio-button :value="30">30 天</a-radio-button>
                <a-radio-button :value="90">90 天</a-radio-button>
              </a-radio-group>
            </div>
          </div>

          <div v-if="loading" class="loading-state">
            <Loader2 :size="32" class="spin" />
            <span>加载中...</span>
          </div>

          <template v-else>
            <div class="metrics-row">
              <div class="metric-item">
                <div class="metric-value">{{ formatNumber(totalTokens) }}</div>
                <div class="metric-label">总 Token</div>
                <div class="metric-sub">输入 {{ formatNumber(Number(stats.totalInputTokens || 0)) }} / 输出 {{ formatNumber(Number(stats.totalOutputTokens || 0)) }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-value">{{ formatNumber(Number(stats.totalRuns || 0)) }}</div>
                <div class="metric-label">运行次数</div>
              </div>
              <div class="metric-item">
                <div class="metric-value">{{ Number(stats.cacheHitRate || 0).toFixed(1) }}%</div>
                <div class="metric-label">缓存命中率</div>
              </div>
              <div class="metric-item">
                <div class="metric-value">{{ formatLatency(Number(stats.avgLatencyMs || 0)) }}</div>
                <div class="metric-label">平均延迟</div>
              </div>
            </div>
          </template>
        </div>
      </div>

        <!-- 暖白趋势区：组合图 -->
        <div class="trend-section">
          <div class="trend-header">
            <h2 class="section-title">每日趋势</h2>
            <div class="legend">
              <div class="legend-item">
                <span class="legend-swatch bar"></span>
                <span>每日总量</span>
              </div>
              <div class="legend-item">
                <span class="legend-swatch line"></span>
                <span>输入趋势</span>
              </div>
            </div>
          </div>

          <div v-if="chartData.length > 0" class="combo-chart-wrapper">
          <div class="combo-chart">
            <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" preserveAspectRatio="none" class="combo-svg">
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#C85A3E" stop-opacity="0.35" />
                  <stop offset="100%" stop-color="#C85A3E" stop-opacity="0.9" />
                </linearGradient>
              </defs>

              <!-- 水平网格线 -->
              <line class="combo-grid" :x1="0" :y1="gridBaseline" :x2="chartWidth" :y2="gridBaseline" />
              <line class="combo-grid dashed" :x1="0" :y1="gridBaseline * 0.75" :x2="chartWidth" :y2="gridBaseline * 0.75" />
              <line class="combo-grid dashed" :x1="0" :y1="gridBaseline * 0.5" :x2="chartWidth" :y2="gridBaseline * 0.5" />
              <line class="combo-grid dashed" :x1="0" :y1="gridBaseline * 0.25" :x2="chartWidth" :y2="gridBaseline * 0.25" />

              <!-- 柱状图：每日总量 -->
              <g class="combo-bars">
                <rect
                  v-for="(d, i) in chartData"
                  :key="'bar-' + i"
                  class="combo-bar"
                  :x="barX(i)"
                  :y="barY(d.total)"
                  :width="barWidth"
                  :height="barHeight(d.total)"
                  rx="3"
                  @mouseenter="showTooltip($event, d)"
                  @mouseleave="hideTooltip"
                />
              </g>

              <!-- 折线图：输入趋势叠加 -->
              <path class="combo-area" :d="areaPath" />
              <path class="combo-line" :d="linePath" />
              <circle
                v-for="(d, i) in chartData"
                :key="'dot-' + i"
                class="combo-dot"
                :cx="lineX(i)"
                :cy="lineY(d.input)"
                r="3"
              />
            </svg>
            <div ref="tooltipRef" class="combo-tooltip">
              <div class="tip-row"><span class="tip-label">日期</span><span>{{ activeTip?.date || '—' }}</span></div>
              <div class="tip-row"><span class="tip-label">总量</span><span>{{ formatNumber(activeTip?.total || 0) }}</span></div>
              <div class="tip-row"><span class="tip-label">输入</span><span>{{ formatNumber(activeTip?.input || 0) }}</span></div>
            </div>
          </div>

          <!-- X 轴日期标签 -->
          <div class="x-labels">
            <span v-for="(d, i) in chartData" :key="'xlabel-' + i" class="x-label">{{ formatDateShort(d.date) }}</span>
          </div>
          </div>

          <div v-else class="empty-chart">
            <BarChart3 :size="40" />
            <p>暂无用量数据</p>
          </div>

          <!-- 近期运行记录 -->
          <div v-if="chartData.length > 0" class="run-list">
            <h3 class="section-title">近期运行记录</h3>
            <div v-for="(d, i) in chartData.slice().reverse().slice(0, 7)" :key="'run-' + i" class="run-row">
              <span class="run-date">{{ formatDate(d.date) }} · {{ d.runs || 0 }} 次运行</span>
              <span class="run-tokens">
                <span class="token-input">{{ formatNumber(d.input) }} 输入</span>
                <span class="token-divider">/</span>
                <span class="token-output">{{ formatNumber(d.output) }} 输出</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getTokenUsageStats } from '@/api/userController'
import { BarChart3, Loader2 } from '@lucide/vue'

const days = ref(7)
const loading = ref(true)
const stats = ref<API.TokenUsageStatsVO>({})

// 图表几何参数
const chartWidth = 1200
const chartHeight = 280
const gridBaseline = 240 // 底部基线 Y
const barWidth = 36
const barGap = 84 // 柱子中心间距

// 组合图数据：从 dailyTokenUsage 映射，每项含 date / total / input / output / runs
const chartData = computed(() => {
  const daily = stats.value.dailyTokenUsage || []
  return daily.map((d) => ({
    date: d.date || '',
    total: Number(d.inputTokens || 0) + Number(d.outputTokens || 0),
    input: Number(d.inputTokens || 0),
    output: Number(d.outputTokens || 0),
    runs: Number(d.runs || 0),
  }))
})

// 每日总量的最大值，用于柱子高度归一化
const maxTotal = computed(() => Math.max(...chartData.value.map((d) => d.total), 1))
// 输入 token 的最大值，用于折线 Y 坐标归一化
const maxInput = computed(() => Math.max(...chartData.value.map((d) => d.input), 1))

const totalTokens = computed(() => Number(stats.value.totalInputTokens || 0) + Number(stats.value.totalOutputTokens || 0))

const loadData = async () => {
  loading.value = true
  try {
    const res = await getTokenUsageStats({ days: days.value })
    if (res.data.code === 0 && res.data.data) {
      stats.value = res.data.data
    }
  } catch {
    message.error('加载统计数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

// ── 柱状图坐标计算 ──
const barX = (i: number) => i * barGap + 30
const barY = (total: number) => gridBaseline - (total / maxTotal.value) * (gridBaseline - 24)
const barHeight = (total: number) => (total / maxTotal.value) * (gridBaseline - 24)

// ── 折线图坐标计算（与柱子中心对齐） ──
const lineX = (i: number) => i * barGap + 30 + barWidth / 2
const lineY = (input: number) => gridBaseline - (input / maxInput.value) * (gridBaseline - 24)

// 折线路径
const linePath = computed(() => {
  return chartData.value.map((d, i) => `${i === 0 ? 'M' : 'L'} ${lineX(i)},${lineY(d.input)}`).join(' ')
})

// 折线下方面积路径
const areaPath = computed(() => {
  if (chartData.value.length === 0) return ''
  const points = chartData.value.map((d, i) => `${lineX(i)},${lineY(d.input)}`).join(' L ')
  const lastX = lineX(chartData.value.length - 1)
  const firstX = lineX(0)
  return `M ${firstX},${gridBaseline} L ${points} L ${lastX},${gridBaseline} Z`
})

// tooltip
const tooltipRef = ref<HTMLElement | null>(null)
const activeTip = ref<{ date: string; total: number; input: number; output: number } | null>(null)

const showTooltip = (e: MouseEvent, d: { date: string; total: number; input: number; output: number }) => {
  activeTip.value = d
  if (tooltipRef.value) {
    const chartEl = (e.currentTarget as HTMLElement).closest('.combo-chart') as HTMLElement
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    const chartRect = chartEl.getBoundingClientRect()
    tooltipRef.value.style.left = rect.left - chartRect.left + rect.width / 2 + 'px'
    tooltipRef.value.style.top = rect.top - chartRect.top + 'px'
    tooltipRef.value.classList.add('visible')
  }
}

const hideTooltip = () => {
  activeTip.value = null
  if (tooltipRef.value) tooltipRef.value.classList.remove('visible')
}

const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return String(num)
}

const formatLatency = (ms: number) => {
  if (ms >= 1000) return (ms / 1000).toFixed(1) + 's'
  return Math.round(ms) + 'ms'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

const formatDateShort = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}
</script>

<style scoped>
.dashboard-page {
  min-height: calc(100vh - 64px);
  background: var(--color-background);
}

.dashboard-container {
  max-width: var(--container-widescreen);
  margin: 0 auto;
}

/* ── 深色区域：背景全宽，内容居中约束 ── */
.dark-section {
  background: var(--color-hero-bg);
  width: 100vw;
  margin-left: calc(-50vw + 50%);
}

.dark-section-inner {
  max-width: var(--container-widescreen);
  margin: 0 auto;
  padding: var(--space-section-tight) var(--space-page-x);
}

.page-title-block {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 48px;
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
  color: var(--color-text-on-dark);
}

.page-subtitle {
  font-size: 16px;
  color: var(--color-text-on-dark-secondary);
  margin-top: 8px;
}

.time-toggle-wrap {
  margin-left: auto;
}

/* 深色背景下 radio 按钮适配 */
.time-toggle-wrap :deep(.ant-radio-group) {
  display: flex;
  gap: var(--space-xs);
}

.time-toggle-wrap :deep(.ant-radio-button-wrapper) {
  padding: 6px 16px;
  background: transparent !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  color: rgba(255, 255, 255, 0.6) !important;
  font-size: 14px;
  height: auto;
  line-height: 1.4;
  border-radius: var(--radius-badge) !important;
}

.time-toggle-wrap :deep(.ant-radio-button-wrapper-checked) {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.4) !important;
  color: #fff !important;
}

.time-toggle-wrap :deep(.ant-radio-button-wrapper:not(:first-child)::before) {
  display: none;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-section-tight) 0;
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

/* ── 深色指标区 ── */
.metrics-row {
  display: flex;
  align-items: stretch;
  margin-top: 48px;
}

.metric-item {
  flex: 1;
  text-align: center;
  padding: var(--space-lg) 0;
  position: relative;
}

.metric-item:not(:last-child)::after {
  content: '';
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 1px;
  height: 60%;
  background: rgba(255, 255, 255, 0.15);
}

.metric-value {
  font-family: var(--font-heading);
  font-size: var(--size-metric);
  font-weight: 700;
  letter-spacing: -1px;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  margin-bottom: 8px;
  color: #fff;
}

.metric-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.metric-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

/* ── 暖白趋势区 ── */
.trend-section {
  background: var(--color-background);
  padding: var(--space-section-tight) var(--space-page-x);
}

.trend-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: var(--space-field);
}

.section-title {
  font-family: var(--font-heading);
  font-size: var(--size-section-title);
  font-weight: 600;
  color: var(--color-text);
}

.legend {
  display: flex;
  gap: var(--space-lg);
  font-size: 12px;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-swatch {
  width: 12px;
  height: 12px;
}

.legend-swatch.bar {
  background: var(--color-cta);
}

.legend-swatch.line {
  height: 2px;
  background: #2c4258;
  opacity: 0.55;
  width: 16px;
}

/* ── 组合图 wrapper ── */
.combo-chart-wrapper {
  margin-bottom: 16px;
}

/* ── 组合图：280px 高 ── */
.combo-chart {
  position: relative;
  height: 280px;
}

.combo-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.combo-grid {
  stroke: var(--color-border);
  stroke-width: 0.5;
}

.combo-grid.dashed {
  stroke-dasharray: 3, 3;
}

/* 柱状图：陶土橙渐变 + 圆角 + glow */
.combo-bars {
  filter: drop-shadow(0 4px 12px rgba(200, 90, 62, 0.18));
}

.combo-bar {
  fill: url(#barGradient);
  transition: opacity var(--transition-fast);
  cursor: pointer;
}

.combo-bar:hover {
  opacity: 0.88;
}

/* 折线图：柔和深蓝灰极细线 */
.combo-line {
  fill: none;
  stroke: #2c4258;
  stroke-width: 1.5;
  stroke-linejoin: round;
  stroke-linecap: round;
  stroke-opacity: 0.55;
}

.combo-area {
  fill: #2c4258;
  opacity: 0.04;
}

.combo-dot {
  fill: #2c4258;
  fill-opacity: 0.55;
  transition: all var(--transition-fast);
}

.combo-dot:hover {
  fill: var(--color-cta);
  fill-opacity: 1;
}

/* ── X 轴日期标签 ── */
.x-labels {
  display: flex;
  justify-content: space-between;
  padding: 0 4px;
}

.x-label {
  font-size: 11px;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

/* tooltip */
.combo-tooltip {
  position: absolute;
  background: var(--color-primary);
  color: #fff;
  padding: 8px 12px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-fast);
  transform: translate(-50%, -100%);
  margin-top: -8px;
  border-radius: var(--radius-badge);
  box-shadow: var(--shadow-md);
}

.combo-tooltip.visible {
  opacity: 1;
}

.tip-row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  line-height: 1.6;
}

.tip-label {
  color: rgba(255, 255, 255, 0.5);
}

.empty-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-block);
  color: var(--color-text-muted);
}

/* ── 运行记录列表 ── */
.run-list {
  margin-top: var(--space-block);
}

.run-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) 0;
  border-bottom: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: transform var(--transition-fast);
}

.run-row:hover {
  transform: translateX(4px);
}

.run-date {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.run-tokens {
  font-family: var(--font-heading);
  font-size: 14px;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.token-input {
  color: var(--color-cta);
  font-weight: 600;
}

.token-divider {
  color: var(--color-text-muted);
  margin: 0 4px;
}

.token-output {
  color: var(--color-text-secondary);
  font-weight: 500;
}

@media (max-width: 768px) {
  .dark-section-inner {
    padding: var(--space-section-tight) var(--space-page-x-sm);
  }

  .page-title-block {
    flex-direction: column;
    gap: var(--space-md);
  }

  .time-toggle-wrap {
    margin-left: 0;
  }

  .trend-section {
    padding: var(--space-section-tight) var(--space-page-x-sm);
  }

  .metrics-row {
    flex-direction: column;
  }

  .metric-item:not(:last-child)::after {
    display: none;
  }

  .metric-item:not(:last-child) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  }

  .metric-value {
    font-size: 36px;
  }

  .page-title {
    font-size: 32px;
  }

  .trend-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
  }
}
</style>
