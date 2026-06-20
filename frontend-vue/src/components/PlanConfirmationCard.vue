<template>
  <div class="plan-confirmation">
    <div class="confirmation-header">
      <span>AI 已生成实施计划</span>
    </div>

    <div class="outline-title">{{ outline.title }}</div>
    <div class="outline-summary">{{ outline.summary }}</div>

    <div class="outline-section">
      <div class="section-label">实施步骤</div>
      <div v-for="(step, i) in outline.steps" :key="i" class="step-item">
        <span class="step-num">{{ i + 1 }}</span>
        <span>{{ step }}</span>
      </div>
    </div>

    <div v-if="outline.risks.length" class="outline-section">
      <div class="section-label">潜在风险</div>
      <div v-for="(risk, i) in outline.risks" :key="i" class="risk-item">
        <span class="risk-marker" />
        <span>{{ risk }}</span>
      </div>
    </div>

    <div v-if="outline.assumptions.length" class="outline-section">
      <div class="section-label">前提假设</div>
      <div v-for="(a, i) in outline.assumptions" :key="i" class="assumption-item">
        <span>{{ a }}</span>
      </div>
    </div>

    <div class="confirmation-actions">
      <a-button @click="$emit('cancel')">取消</a-button>
      <a-button type="primary" @click="$emit('confirm')">确认，开始生成</a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface PlanOutline {
  title: string
  summary: string
  steps: string[]
  risks: string[]
  assumptions: string[]
}

defineProps<{ outline: PlanOutline }>()
defineEmits<{ confirm: []; cancel: [] }>()
</script>

<style scoped>
.plan-confirmation {
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface);
  overflow: hidden;
}

.confirmation-header {
  padding: 14px 18px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.outline-title {
  padding: 16px 18px 4px;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
}

.outline-summary {
  padding: 6px 18px 14px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.outline-section {
  padding: 0 18px 14px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  font-size: 13px;
  color: var(--color-text);
}

.step-num {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: rgba(34, 197, 94, 0.15);
  color: var(--color-cta);
  font-size: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.risk-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.risk-marker {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-warning);
  flex-shrink: 0;
  margin-top: 6px;
}

.assumption-item {
  font-size: 12px;
  color: var(--color-text-muted);
  padding: 2px 0;
}

.confirmation-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 18px;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
}
</style>
