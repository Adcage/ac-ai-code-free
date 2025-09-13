<template>
  <a-layout-footer class="global-footer">
    <div class="footer-content">
      <p class="copyright">
        AI Code Free by
        <a
          href="https://github.com/Adcage"
          target="_blank"
          rel="noopener noreferrer"
          class="github-link"
        >
          @Adcage
        </a>
      </p>
    </div>
  </a-layout-footer>
</template>

<script lang="ts" setup>
// 无需额外的逻辑
</script>

<style scoped>
.global-footer {
  background: #f0f2f5;
  border-top: 1px solid #d9d9d9;
  padding: 16px 0;
  margin-top: auto;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  text-align: center;
}

.copyright {
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.github-link {
  color: #1890ff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.github-link:hover {
  color: #40a9ff;
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .footer-content {
    padding: 0 16px;
  }

  .copyright {
    font-size: 13px;
  }
}

@media (max-width: 480px) {
  .footer-content {
    padding: 0 12px;
  }

  .copyright {
    font-size: 12px;
  }
}
</style>
