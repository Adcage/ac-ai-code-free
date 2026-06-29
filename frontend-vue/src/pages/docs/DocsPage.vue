<template>
  <div class="docs-page">
    <div class="docs-container">
      <div class="page-title-block">
        <div class="accent-bar"></div>
        <div>
          <h1 class="page-title">帮助中心</h1>
        </div>
      </div>

      <div class="docs-layout">
        <div class="docs-left">
          <div class="docs-section-title">使用指南</div>

          <div v-for="(item, idx) in guides" :key="idx" class="guide-item">
            <span class="guide-num">{{ String(idx + 1).padStart(2, '0') }}</span>
            <h3 class="guide-title">{{ item.title }}</h3>
            <p class="guide-desc">{{ item.desc }}</p>
          </div>
        </div>

        <div class="docs-right">
          <div class="docs-section-title">常见问题</div>

          <div v-for="(item, idx) in faqs" :key="idx" class="faq-item">
            <h4 class="faq-title">{{ item.title }}</h4>
            <p class="faq-desc">{{ item.desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
const guides = [
  {
    title: '创建你的第一个应用',
    desc: '从模板开始或从零构建，只需几分钟即可创建功能完备的 AI 应用。选择适合你的模型配置，设置应用参数，即可发布到探索广场。',
  },
  {
    title: '理解 Token 计费',
    desc: 'Token 是 AI 模型处理文本的基本单位。输入和输出都会消耗 Token，不同模型的计费标准不同。专业版用户享有更优惠的 Token 单价。',
  },
  {
    title: '优化提示词技巧',
    desc: '清晰、具体的提示词能获得更好的输出效果。使用角色设定、示例输出、分步指令等技巧，让你的 AI 应用更加智能和精准。',
  },
  {
    title: '部署与分享',
    desc: '一键部署你的应用到云端，获取专属访问链接。支持自定义域名、访问权限控制和版本管理，轻松将应用分享给团队成员或公开社区。',
  },
]

const faqs = [
  {
    title: '免费版有什么限制？',
    desc: '免费版每月提供 10,000 Token，支持基础模型和公开应用创建。如需更多 Token 或私有应用，请升级至专业版。',
  },
  {
    title: '如何计算 Token 用量？',
    desc: 'Token 用量根据输入和输出的字符数计算，不同语言字符对应的 Token 数不同。中文约 1.5 字符/Token，英文约 4 字符/Token。',
  },
  {
    title: '支持哪些模型？',
    desc: '目前支持 GPT-4、Claude、文心一言等主流模型。专业版用户可访问全部模型，企业版支持自定义模型部署。',
  },
  {
    title: '数据安全如何保障？',
    desc: '所有数据传输采用 TLS 加密，存储数据经过 AES-256 加密。企业版支持私有化部署，数据完全隔离。',
  },
  {
    title: '如何取消订阅？',
    desc: '随时可在账户设置中取消订阅，取消后当前计费周期结束前仍可继续使用。已支付的款项不予退还。',
  },
]
</script>

<style scoped>
.docs-page {
  min-height: calc(100vh - 64px);
  background: var(--color-background);
}

.docs-container {
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

/* ── 两栏布局：60% 使用指南 + 35% FAQ ── */
.docs-layout {
  display: grid;
  grid-template-columns: 60% 35%;
  gap: 5%;
  padding-bottom: var(--space-section);
}

.docs-section-title {
  font-family: var(--font-heading);
  font-size: 14px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--color-text-muted);
  margin-bottom: var(--space-block);
}

/* ── 使用指南条目 ── */
.guide-item {
  margin-bottom: var(--space-guide-item);
  padding-bottom: var(--space-guide-item);
  border-bottom: 1px solid var(--color-border);
}

.guide-item:last-child {
  border-bottom: none;
}

.guide-num {
  font-family: var(--font-heading);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-cta);
  font-variant-numeric: tabular-nums;
  margin-bottom: 12px;
  display: block;
}

.guide-title {
  font-family: var(--font-heading);
  font-size: var(--size-guide-title);
  font-weight: 600;
  margin-bottom: 12px;
  letter-spacing: -0.3px;
  color: var(--color-text);
}

.guide-desc {
  font-size: 16px;
  color: var(--color-text-secondary);
  line-height: 1.8;
}

/* ── FAQ 条目 ── */
.faq-item {
  margin-bottom: var(--space-faq-item);
}

.faq-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.5;
  color: var(--color-text);
}

.faq-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

@media (max-width: 1024px) {
  .docs-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .docs-container {
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
