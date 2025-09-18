<template>
  <a-layout-header class="global-header">
    <!-- 左侧：Logo 和标题 -->

    <div class="header-content">
      <a-col class="header-left">
        <div class="logo-container">
          <img alt="AI Code Free" class="logo" src="/logo.png" />
          <span class="site-title">AI Code Free</span>
        </div>
      </a-col>

      <!-- 中间：导航菜单 -->
      <a-col flex="auto">
        <a-menu v-model:selectedKeys="selectedKeys" mode="horizontal" :items="menuItems" @click="handleMenuClick" />
      </a-col>

      <!-- 右侧：用户信息 -->
      <a-col class="header-right">
        <div v-if="loginUserStore.loginUser.id">
          <a-dropdown>
            <a-space align="center">
              <!-- <a-avatar :src="loginUserStore.loginUser.userAvatar" />-->
              <div>
                <UserOutlined class="avatarIcon" />
              </div>
              {{ loginUserStore?.loginUser?.userName }}
            </a-space>
            <template #overlay>
              <a-menu>
                <a-menu-item key="logout">
                  <a-menu-item @click="handleLogout">
                    <LogoutOutlined />
                    退出登录
                  </a-menu-item>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
        <div v-else>
          <a-button href="/user/login" type="primary"> 登录</a-button>
        </div>
      </a-col>
    </div>
  </a-layout-header>
</template>

<script lang="ts" setup>
import { computed, h, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useLoginUserStore } from '@/stores/LoginUser.ts'
import { UsergroupAddOutlined, HomeOutlined, LogoutOutlined, UserOutlined } from '@ant-design/icons-vue'
import type { MenuProps } from 'ant-design-vue'

const router = useRouter()
const selectedKeys = ref<string[]>(['home'])

//TODO 后续删除这里的fetch,毕竟并不是测试代码
const loginUserStore = useLoginUserStore()
loginUserStore.fetchLoginUser()

// 菜单配置项
const originItems = [
  {
    key: '/',
    icon: () => h(HomeOutlined),
    label: '主页',
    title: '主页',
  },
  {
    key: '/admin/userManage',
    icon: () => h(UsergroupAddOutlined),
    label: '用户管理',
    title: '用户管理',
  },
]

// 过滤菜单项
const filterMenus = (menus = [] as MenuProps['items']) => {
  return menus?.filter((menu) => {
    const menuKey = menu?.key as string
    if (menuKey?.startsWith('/admin')) {
      const loginUser = loginUserStore.loginUser
      if (!loginUser || loginUser.userRole !== 'admin') {
        return false
      }
    }
    return true
  })
}

// 展示在菜单的路由数组
const menuItems = computed<MenuProps['items']>(() => filterMenus(originItems))

// 处理菜单点击
const handleMenuClick = ({ key }: { key: string }) => {
  const item = originItems.find((item) => item.key === key)
  if (item) {
    router.push(item.key)
  }
}

const handleLogout = () => {
  loginUserStore.logout()
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
  cursor: pointer;
}

.avatarIcon {
  font-size: 24px;
  border: 2px solid black;
  padding: 5px;
  border-radius: 50%;
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
