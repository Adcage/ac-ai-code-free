<template>
  <a-layout-header class="global-header">
    <!-- 左侧：Logo 和标题 -->

    <div class="header-content">
      <div class="header-left">
        <div class="logo-container">
          <img alt="AI Code Free" class="logo" src="/ai-free-logo.png" />
          <span class="site-title">AI Code Free</span>
        </div>
      </div>

      <!-- 中间：导航菜单 -->
      <div class="header-center">
        <a-menu
          v-model:selectedKeys="selectedKeys"
          :items="menuItems"
          class="header-menu"
          mode="horizontal"
          @click="handleMenuClick"
        />
      </div>

      <!-- 右侧：用户信息 -->
      <div class="header-right">
        <a-button type="primary" @click="handleLogin"> 登录</a-button>
      </div>
    </div>
  </a-layout-header>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const selectedKeys = ref<string[]>(['home'])

// 菜单配置
const menuItems = [
  {
    key: 'home',
    label: '首页',
    path: '/'
  },
  {
    key: 'about',
    label: '关于',
    path: '/about'
  },
  {
    key: 'features',
    label: '功能',
    path: '/features'
  },
  {
    key: 'contact',
    label: '联系我们',
    path: '/contact'
  }
]

// 处理菜单点击
const handleMenuClick = ({ key }: { key: string }) => {
  const item = menuItems.find((item) => item.key === key)
  if (item) {
    router.push(item.path)
  }
}

// 处理登录
const handleLogin = () => {
  console.log('登录功能待实现')
}
</script>

<style scoped>
.global-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-content {
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 64px;
  width: 100%;
  margin: 0 auto;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  height: 32px;
  width: auto;
}

.site-title {
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.header-center {
  display: flex;
  justify-content: flex-start;
  margin-left: 40px;
  flex: 1;
}

.header-menu {
  border-bottom: none;
  background: transparent;
}

.header-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }

  .site-title {
    display: none;
  }

  .header-center {
    display: none;
  }

  .header-menu {
    display: none;
  }
}

@media (max-width: 480px) {
  .header-content {
    padding: 0 12px;
  }

  .logo {
    height: 28px;
  }
}
</style>
