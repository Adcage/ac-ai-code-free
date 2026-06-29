<template>
  <div class="auth-shell">
    <div class="auth-background">
      <div class="auth-orb auth-orb-primary"></div>
      <div class="auth-orb auth-orb-secondary"></div>
      <div class="auth-grid"></div>
    </div>

    <div class="auth-topbar">
      <RouterLink to="/" class="home-link">
        <img alt="原象 Morpha" class="home-logo" src="/brand/logo-light.svg" />
        <div class="home-copy">
          <span class="home-title">原象 Morpha</span>
          <span class="home-subtitle">AI 驱动的设计创作平台</span>
        </div>
      </RouterLink>
      <div class="topbar-note">Creative Workspace</div>
    </div>

    <main class="auth-stage">
      <section class="story-panel">
        <div class="story-badge">{{ storyBadge }}</div>
        <h1 class="story-title">{{ storyTitle }}</h1>
        <p class="story-description">{{ storyDescription }}</p>

        <div class="story-highlights">
          <article v-for="item in highlights" :key="item.title" class="highlight-card">
            <div class="highlight-icon">
              <component :is="item.icon" :size="18" />
            </div>
            <div class="highlight-copy">
              <h2>{{ item.title }}</h2>
              <p>{{ item.description }}</p>
            </div>
          </article>
        </div>

        <div class="workflow-card">
          <div class="workflow-head">
            <span class="workflow-kicker">创作流程</span>
            <ArrowUpRight :size="16" />
          </div>
          <div class="workflow-message">“帮我生成一个暖色极简的作品集首页，并保留移动端体验。”</div>
          <div class="workflow-steps">
            <div v-for="step in workflowSteps" :key="step.title" class="workflow-step">
              <span class="workflow-index">{{ step.index }}</span>
              <div>
                <div class="workflow-title">{{ step.title }}</div>
                <div class="workflow-text">{{ step.description }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel-side">
        <div class="auth-card">
          <div class="card-brand">
            <img alt="原象 Morpha" class="card-brand-logo" src="/brand/logo-dark.svg" />
            <span class="card-brand-name">原象 Morpha</span>
          </div>
          <div class="card-eyebrow">{{ panelEyebrow }}</div>
          <h2 class="card-title">{{ title }}</h2>
          <p class="card-subtitle">{{ subtitle }}</p>

          <div class="form-slot">
            <slot></slot>
          </div>

          <div class="switch-row">
            <span>{{ switchPrompt }}</span>
            <RouterLink :to="switchTo">{{ switchLinkText }}</RouterLink>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { ArrowUpRight, MessageSquareMore, PanelsTopLeft, Rocket } from '@lucide/vue'

interface Props {
  panelEyebrow: string
  title: string
  subtitle: string
  switchPrompt: string
  switchLinkText: string
  switchTo: string
  storyBadge?: string
  storyTitle?: string
  storyDescription?: string
}

const props = withDefaults(defineProps<Props>(), {
  storyBadge: 'AI Creative Workflow',
  storyTitle: '继续推进你的下一次创作',
  storyDescription: '从提示词、页面预览到发布上线，原象把完整创作过程收拢在同一个工作台里，让想法更快落地。',
})

const highlights = computed(() => [
  {
    icon: MessageSquareMore,
    title: '对话生成',
    description: '从一句自然语言开始，逐步收敛页面结构、风格与内容。',
  },
  {
    icon: PanelsTopLeft,
    title: '实时预览',
    description: '边生成边查看结果，避免在抽象提示词和真实界面之间来回跳。',
  },
  {
    icon: Rocket,
    title: '部署上线',
    description: '完成设计后直接进入发布链路，让作品尽快从草图走向可分享状态。',
  },
])

const workflowSteps = [
  {
    index: '01',
    title: '描述想法',
    description: '用自然语言定义风格、内容与场景。',
  },
  {
    index: '02',
    title: '生成预览',
    description: '实时查看页面并继续调整。',
  },
  {
    index: '03',
    title: '发布成品',
    description: '在工作台内完成部署与版本沉淀。',
  },
]
</script>

<style scoped>
.auth-shell {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(212, 148, 76, 0.24), transparent 32%),
    radial-gradient(circle at 85% 18%, rgba(200, 90, 62, 0.18), transparent 26%),
    linear-gradient(135deg, #12202d 0%, #1a2f40 45%, #243748 100%);
  color: var(--color-text-on-dark);
}

.auth-background {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.auth-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(12px);
  opacity: 0.85;
}

.auth-orb-primary {
  top: 10%;
  left: -4%;
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(212, 148, 76, 0.22) 0%, rgba(212, 148, 76, 0) 72%);
}

.auth-orb-secondary {
  right: 6%;
  bottom: 12%;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(200, 90, 62, 0.22) 0%, rgba(200, 90, 62, 0) 72%);
}

.auth-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 120px 120px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.48), transparent 85%);
  opacity: 0.18;
}

.auth-topbar {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  padding: 28px 40px 0;
}

.home-link {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  text-decoration: none;
}

.home-logo {
  width: 40px;
  height: 40px;
}

.home-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.home-title {
  font-family: var(--font-heading);
  font-size: 17px;
  font-weight: 600;
  color: #fff;
  letter-spacing: -0.02em;
}

.home-subtitle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.62);
}

.topbar-note {
  padding: 10px 14px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.auth-stage {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(360px, 440px);
  gap: 56px;
  align-items: center;
  min-height: calc(100vh - 88px);
  max-width: 1320px;
  margin: 0 auto;
  padding: 28px 40px 40px;
}

.story-panel {
  max-width: 660px;
}

.story-badge {
  display: inline-flex;
  align-items: center;
  margin-bottom: 24px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(200, 90, 62, 0.12);
  border: 1px solid rgba(200, 90, 62, 0.28);
  color: #f2b7a3;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.story-title {
  margin: 0;
  font-family: var(--font-heading);
  font-size: clamp(44px, 5vw, 72px);
  line-height: 1.02;
  letter-spacing: -0.05em;
  color: #fff7f2;
  text-wrap: balance;
}

.story-description {
  max-width: 580px;
  margin: 22px 0 0;
  font-size: 17px;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.72);
}

.story-highlights {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 36px;
}

.highlight-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 180px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 22px;
  backdrop-filter: blur(16px);
  box-shadow: 0 20px 45px rgba(7, 16, 23, 0.18);
}

.highlight-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: rgba(242, 183, 163, 0.12);
  color: #f4b49e;
}

.highlight-copy h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #fff7f2;
}

.highlight-copy p {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.68);
}

.workflow-card {
  margin-top: 24px;
  padding: 24px;
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.09) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 24px 60px rgba(7, 16, 23, 0.22);
  backdrop-filter: blur(18px);
}

.workflow-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: rgba(255, 255, 255, 0.64);
}

.workflow-kicker {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.workflow-message {
  margin-top: 18px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff3eb;
  font-size: 15px;
  line-height: 1.7;
}

.workflow-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.workflow-step {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.workflow-index {
  font-family: var(--font-heading);
  font-size: 13px;
  font-weight: 700;
  color: #f4b49e;
}

.workflow-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff7f2;
}

.workflow-text {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.62);
}

.panel-side {
  display: flex;
  justify-content: flex-end;
}

.auth-card {
  width: min(100%, 440px);
  padding: 30px;
  border-radius: 32px;
  background: rgba(252, 249, 245, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.65);
  box-shadow:
    0 28px 80px rgba(12, 18, 24, 0.34),
    0 4px 16px rgba(255, 255, 255, 0.2) inset;
  color: var(--color-text);
}

.card-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.card-brand-logo {
  width: 30px;
  height: 30px;
}

.card-brand-name {
  font-family: var(--font-heading);
  font-size: 15px;
  font-weight: 600;
  color: var(--color-primary);
}

.card-eyebrow {
  margin-top: 26px;
  color: var(--color-cta);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.card-title {
  margin: 10px 0 0;
  font-family: var(--font-heading);
  font-size: 34px;
  line-height: 1.05;
  letter-spacing: -0.04em;
  color: var(--color-text);
}

.card-subtitle {
  margin: 14px 0 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-secondary);
}

.form-slot {
  margin-top: 28px;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 20px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.switch-row a {
  color: var(--color-cta);
  font-weight: 600;
  text-decoration: none;
}

.switch-row a:hover {
  color: var(--color-cta-hover);
}

:deep(.ant-form-item) {
  margin-bottom: 20px;
}

:deep(.ant-form-item:last-child) {
  margin-bottom: 0;
}

:deep(.ant-form-item-label > label) {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 600;
}

:deep(.ant-input),
:deep(.ant-input-affix-wrapper) {
  border-radius: 14px;
  border-color: rgba(220, 207, 196, 0.95);
  background: rgba(255, 255, 255, 0.86);
  color: var(--color-text);
  box-shadow: none;
}

:deep(.ant-input) {
  min-height: 50px;
  padding: 12px 16px;
}

:deep(.ant-input-affix-wrapper) {
  min-height: 50px;
  padding: 0 14px;
}

:deep(.ant-input-affix-wrapper input.ant-input) {
  min-height: auto;
  padding: 0 6px;
}

:deep(.ant-input::placeholder),
:deep(.ant-input-affix-wrapper input::placeholder) {
  color: var(--color-text-muted);
}

:deep(.ant-input:focus),
:deep(.ant-input-focused),
:deep(.ant-input-affix-wrapper:focus),
:deep(.ant-input-affix-wrapper-focused) {
  border-color: rgba(200, 90, 62, 0.75);
  box-shadow: 0 0 0 4px rgba(200, 90, 62, 0.12);
}

:deep(.auth-submit-btn) {
  width: 100%;
  min-height: 50px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--color-cta) 0%, #d97252 100%);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  font-family: var(--font-body);
  cursor: pointer;
  transition:
    transform var(--transition-normal),
    box-shadow var(--transition-normal),
    filter var(--transition-normal);
  box-shadow: 0 18px 28px rgba(200, 90, 62, 0.24);
}

:deep(.auth-submit-btn:hover) {
  transform: translateY(-1px);
  filter: brightness(1.02);
  box-shadow: 0 20px 32px rgba(200, 90, 62, 0.28);
}

:deep(.auth-submit-btn:active) {
  transform: translateY(0);
}

@media (max-width: 1180px) {
  .auth-stage {
    grid-template-columns: minmax(0, 1fr);
    gap: 28px;
    padding-top: 20px;
  }

  .story-panel {
    max-width: none;
  }

  .panel-side {
    justify-content: flex-start;
  }
}

@media (max-width: 860px) {
  .auth-topbar {
    padding: 20px 20px 0;
  }

  .auth-stage {
    min-height: auto;
    padding: 18px 20px 24px;
  }

  .panel-side {
    order: -1;
  }

  .story-title {
    font-size: 38px;
  }

  .story-description {
    font-size: 15px;
  }

  .story-highlights,
  .workflow-steps {
    grid-template-columns: 1fr;
  }

  .highlight-card {
    min-height: auto;
  }

  .auth-card {
    width: 100%;
    padding: 24px;
    border-radius: 28px;
  }

  .card-title {
    font-size: 30px;
  }
}

@media (max-width: 520px) {
  .home-subtitle,
  .topbar-note {
    display: none;
  }

  .story-badge {
    margin-bottom: 18px;
  }

  .story-title {
    font-size: 32px;
  }

  .auth-card {
    padding: 22px 18px;
  }

  .card-title {
    font-size: 28px;
  }
}
</style>
