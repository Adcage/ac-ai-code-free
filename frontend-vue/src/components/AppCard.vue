<template>
  <a-card
    hoverable
    :class="['app-card', `size-${size}`, { 'no-border': !bordered }]"
    :body-style="{ padding: 0 }"
    @click="handleCardClick"
  >
    <template #cover>
      <div class="card-cover-wrapper" :style="{ height: coverHeight + 'px' }">
        <img :src="app.cover || defaultCover" class="card-cover" />

        <!-- 封面右上角标签插槽 -->
        <div v-if="tagPosition === 'top-right'" class="tag-overlay">
          <slot name="tags">
            <a-tag color="success" v-if="app.deployKey" size="small">已部署</a-tag>
          </slot>
        </div>

        <!-- 悬浮遮罩层：根据 actions 列表渲染按钮 -->
        <div class="card-mask">
          <a-space direction="vertical" :size="12">
            <template v-for="action in computedActions" :key="action">
              <!-- 查看对话 (核心功能，始终为主按钮) -->
              <a-button v-if="action === 'chat'" type="primary" shape="round" class="action-btn" @click.stop="goToApp">
                <template #icon><MessageOutlined /></template>
                查看对话
              </a-button>

              <!-- 查看作品 (部署预览，作为次要按钮) -->
              <a-button
                v-if="action === 'view' && app.deployKey"
                shape="round"
                class="action-btn"
                @click.stop="openDeployUrl"
              >
                <template #icon><EyeOutlined /></template>
                {{ isOwner ? '查看作品' : '立即体验' }}
              </a-button>

              <!-- 编辑 (次要按钮) -->
              <a-button v-if="action === 'edit' && canEdit" shape="round" class="action-btn" @click.stop="goToEdit">
                <template #icon><EditOutlined /></template>
                编辑应用
              </a-button>

              <!-- 删除 (危险操作) -->
              <a-popconfirm
                v-if="action === 'delete' && canEdit"
                title="确定要删除这个应用吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="handleDelete"
              >
                <a-button danger shape="round" class="action-btn" @click.stop>
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </template>
          </a-space>
        </div>
      </div>
    </template>

    <div class="app-card-content">
      <div class="card-info-top">
        <UserAvatar v-if="showUser" :user="app.user" :size="size === 'small' ? 28 : 32" />
        <div class="card-meta">
          <div class="card-header">
            <div class="card-title" :title="app.appName">{{ app.appName }}</div>
            <span v-if="showTime" class="time">{{ formatDate(app.createTime) }}</span>
          </div>
          <div v-if="showUser" class="user-name">{{ app.user?.userName || '匿名用户' }}</div>
        </div>
      </div>
      <div class="card-info-bottom">
        <div class="status-tags">
          <a-tag color="blue" size="small" v-if="app.codeGenType">{{ formatCodeGenType(app.codeGenType) }}</a-tag>
          <a-tag :color="isOwner ? 'green' : 'default'" size="small">{{
            isOwner ? '可下载源码' : '仅作者可下载'
          }}</a-tag>
          <slot name="tags" v-if="tagPosition === 'bottom-left'">
            <a-tag color="success" v-if="app.deployKey" size="small">已部署</a-tag>
          </slot>
        </div>
      </div>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { EyeOutlined, MessageOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { useLoginUserStore } from '@/stores/LoginUser'
import UserAvatar from '@/components/UserAvatar.vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

type CardSize = 'small' | 'default' | 'large'
type ActionType = 'view' | 'chat' | 'edit' | 'delete'

interface Props {
  app: API.AppVO
  showUser?: boolean
  bordered?: boolean
  size?: CardSize
  actions?: ActionType[]
  tagPosition?: 'top-right' | 'bottom-left'
  showTime?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showUser: true,
  bordered: true,
  size: 'default',
  tagPosition: 'bottom-left',
  showTime: true,
})

const emit = defineEmits(['delete', 'edit'])
const router = useRouter()
const loginUserStore = useLoginUserStore()
const defaultCover = 'https://gw.alipayobjects.com/zos/rmsportal/JiqGstEfoWAOHiTxclqi.png'

// 权限判定
const isOwner = computed(() => {
  const loginUser = loginUserStore.loginUser
  return loginUser && loginUser.id === props.app.userId
})

const canEdit = computed(() => {
  const loginUser = loginUserStore.loginUser
  return isOwner.value || loginUser?.userRole === 'admin'
})

// 计算高度
const coverHeight = computed(() => {
  if (props.size === 'small') return 120
  if (props.size === 'large') return 200
  return 160
})

// 计算最终操作列表
const computedActions = computed(() => {
  if (props.actions && props.actions.length > 0) return props.actions
  // 默认行为
  return isOwner.value ? ['view', 'chat'] : ['view']
})

// 跳转逻辑
const goToApp = () => router.push(`/app/generate/${props.app.id}`)
const goToEdit = () => emit('edit', props.app)
const openDeployUrl = () => {
  if (!props.app.deployKey) return
  const deployHost = import.meta.env.VITE_APP_DEPLOY_HOST || 'http://localhost'
  window.open(`${deployHost}/${props.app.deployKey}/`, '_blank')
}

const handleCardClick = () => goToApp()
const handleDelete = () => emit('delete', props.app.id)

const formatDate = (date: any) => {
  if (!date) return ''
  return dayjs(date).fromNow()
}

const formatCodeGenType = (codeGenType?: string) => {
  if (codeGenType === 'single_file') return '单文件'
  if (codeGenType === 'multi-file') return '多文件'
  if (codeGenType === 'vue_project') return 'Vue'
  return '未知'
}
</script>

<style scoped>
.app-card {
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-surface) !important;
  border-color: var(--color-border) !important;
  transition: all var(--transition-normal);
}

.app-card.no-border {
  border: none;
  box-shadow: none;
}

.size-small {
  width: 240px;
}

.size-large {
  width: 320px;
}

.app-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.card-cover-wrapper {
  position: relative;
  overflow: hidden;
  background: var(--color-surface-elevated);
}

.card-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: all 0.5s;
}

.tag-overlay {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
}

.card-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(15, 23, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all var(--transition-normal);
}

.action-btn {
  width: 110px;
}

.app-card:hover .card-mask {
  opacity: 1;
}

.app-card:hover .card-cover {
  transform: scale(1.1);
}

.app-card-content {
  padding: 12px 16px 16px;
}

.card-info-top {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  justify-content: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}

.card-title {
  flex: 1;
  font-weight: 600;
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.4;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.user-name {
  color: var(--color-text-muted);
  font-size: 12px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.card-info-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.time {
  flex-shrink: 0;
  color: var(--color-text-muted);
  font-size: 11px;
}
</style>
