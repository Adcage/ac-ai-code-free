<template>
  <div class="pricing-page">
    <div class="pricing-container">
      <div class="page-title-block">
        <div class="accent-bar"></div>
        <div>
          <h1 class="page-title">定价方案</h1>
          <p class="page-subtitle">从免费开始，随需升级</p>
        </div>
      </div>

      <div class="plans-grid">
        <div class="plan-card">
          <div class="plan-name">免费版</div>
          <div class="plan-price">¥0<span class="plan-period">/月</span></div>
          <ul class="plan-features">
            <li>每月 10,000 Token</li>
            <li>基础模型访问</li>
            <li>社区支持</li>
            <li>公开应用创建</li>
            <li>标准响应速度</li>
          </ul>
          <a-button class="plan-btn ghost" block @click="handleUpgrade">开始使用</a-button>
        </div>

        <div class="plan-card featured">
          <div class="plan-badge">推荐</div>
          <div class="plan-name">专业版</div>
          <div class="plan-price">¥49<span class="plan-period">/月</span></div>
          <ul class="plan-features">
            <li>每月 100,000 Token</li>
            <li>全部模型访问</li>
            <li>优先技术支持</li>
            <li>私有应用创建</li>
            <li>快速响应通道</li>
            <li>API 访问权限</li>
            <li>自定义模型配置</li>
          </ul>
          <a-button type="primary" class="plan-btn filled" block @click="handleUpgrade">立即升级</a-button>
        </div>

        <div class="plan-card">
          <div class="plan-name">企业版</div>
          <div class="plan-price">定制<span class="plan-period">/月</span></div>
          <ul class="plan-features">
            <li>无限 Token</li>
            <li>专属模型部署</li>
            <li>7x24 技术支持</li>
            <li>SSO 单点登录</li>
            <li>SLA 保障</li>
            <li>私有化部署选项</li>
          </ul>
          <a-button class="plan-btn ghost" block @click="handleContact">联系销售</a-button>
        </div>
      </div>

      <p class="pricing-note">所有方案均包含 7 天免费试用</p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { message } from 'ant-design-vue'

const handleUpgrade = () => {
  message.info('即将开放，敬请期待')
}

const handleContact = () => {
  message.info('即将开放，敬请期待')
}
</script>

<style scoped>
.pricing-page {
  min-height: calc(100vh - 64px);
  background: var(--color-background);
}

.pricing-container {
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

/* ── 三列卡片网格：1fr 1.2fr 1fr ── */
.plans-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr;
  gap: var(--space-lg);
  align-items: stretch;
  padding-bottom: var(--space-section);
}

.plan-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: 40px 32px;
  position: relative;
  display: flex;
  flex-direction: column;
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal), transform var(--transition-normal);
}

.plan-card:hover {
  border-color: var(--color-cta);
  box-shadow: var(--shadow-lg);
}

/* 专业版：不对称突出 + 橙边框 + 顶部橙线 + 极淡橙底 + scale + 橙阴影 */
.plan-card.featured {
  background: rgba(200, 90, 62, 0.04);
  border-color: var(--color-cta);
  border-top: 4px solid var(--color-cta);
  padding-top: 36px;
  transform: scale(1.02);
  box-shadow: 0 8px 24px rgba(200, 90, 62, 0.1);
}

.plan-card.featured:hover {
  transform: scale(1.02) translateY(-2px);
  box-shadow: 0 16px 40px rgba(200, 90, 62, 0.16);
}

.plan-badge {
  position: absolute;
  top: -12px;
  left: 32px;
  background: var(--color-cta);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 4px 12px;
  border-radius: var(--radius-badge);
}

.plan-name {
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--color-text);
}

.plan-price {
  font-family: var(--font-heading);
  font-size: var(--size-price);
  font-weight: 700;
  letter-spacing: -2px;
  line-height: 1;
  margin: 24px 0;
  color: var(--color-text);
}

.plan-period {
  font-size: 16px;
  font-weight: 400;
  color: var(--color-text-secondary);
  letter-spacing: 0;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 32px 0;
  flex: 1;
}

.plan-features li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 14px;
  color: var(--color-text-secondary);
}

.plan-features li::before {
  content: '✓';
  color: var(--color-cta);
  font-weight: 700;
  flex-shrink: 0;
}

/* ── 按钮样式 ── */
.plan-btn {
  width: 100%;
  height: auto;
  padding: 14px;
  font-family: var(--font-body);
  font-size: 15px;
  font-weight: 600;
  border: 1px solid var(--color-cta);
  border-radius: var(--radius-badge);
  transition: all var(--transition-fast);
}

.plan-btn.ghost {
  background: none;
  color: var(--color-cta);
}

.plan-btn.ghost:hover {
  background: var(--color-cta);
  color: #fff;
  border-color: var(--color-cta);
}

.plan-btn.filled {
  background: var(--color-cta);
  color: #fff;
  border-color: var(--color-cta);
}

.plan-btn.filled:hover {
  background: var(--color-cta-hover) !important;
  border-color: var(--color-cta-hover) !important;
}

.pricing-note {
  text-align: center;
  margin-top: var(--space-block);
  margin-bottom: var(--space-section);
  font-size: 14px;
  color: var(--color-text-muted);
}

@media (max-width: 1024px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }

  .plan-card.featured {
    transform: none;
  }

  .plan-card.featured:hover {
    transform: translateY(-2px);
  }
}

@media (max-width: 640px) {
  .pricing-container {
    padding: 0 var(--space-page-x-sm);
  }

  .page-title {
    font-size: 32px;
  }

  .page-title-block {
    padding-top: var(--space-section-tight);
  }
}
</style>
