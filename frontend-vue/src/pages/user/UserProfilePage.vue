<template>
  <div class="profile-page">
    <div class="profile-container">
      <div class="profile-header">
        <div class="avatar-section">
          <div class="avatar-upload-wrapper">
            <div class="avatar-circle" :style="avatarStyle" @click="triggerUpload">
              <img v-if="loginUser.userAvatar" :src="loginUser.userAvatar" alt="avatar" class="avatar-img" />
              <span v-else class="avatar-initial">{{ userInitial }}</span>
              <div class="avatar-overlay">
                <Camera :size="20" />
              </div>
            </div>
            <input ref="fileInputRef" type="file" accept="image/jpeg,image/png,image/gif,image/webp" class="hidden-input" @change="handleFileChange" />
          </div>
          <div class="user-meta">
            <h1 class="user-name">{{ loginUser.userName || '未设置昵称' }}</h1>
            <div class="user-tags">
              <span v-if="loginUser.userRole === 'admin'" class="role-tag admin">管理员</span>
              <span v-else class="role-tag">普通用户</span>
            </div>
            <div class="user-time" v-if="loginUser.createTime">
              <Calendar :size="14" />
              <span>注册于 {{ formatDate(loginUser.createTime) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="profile-card">
        <h2 class="section-title">编辑资料</h2>
        <a-form :model="editForm" layout="vertical" @finish="handleSave">
          <a-form-item label="昵称" name="userName">
            <a-input v-model:value="editForm.userName" placeholder="请输入昵称" size="large" />
          </a-form-item>

          <a-form-item label="头像" name="userAvatar">
            <div class="avatar-form-row">
              <a-input v-model:value="editForm.userAvatar" placeholder="点击上方头像上传" size="large" readonly />
              <a-button size="large" @click="triggerUpload" :loading="uploading">
                {{ uploading ? '上传中...' : '上传头像' }}
              </a-button>
            </div>
          </a-form-item>

          <a-form-item label="简介" name="userProfile">
            <a-textarea v-model:value="editForm.userProfile" placeholder="介绍一下自己吧" :rows="4" size="large" />
          </a-form-item>

          <a-form-item>
            <button class="cta-btn" type="submit" :disabled="saving">
              <Loader2 v-if="saving" :size="18" class="spin" />
              {{ saving ? '保存中...' : '保存修改' }}
            </button>
          </a-form-item>
        </a-form>
      </div>

      <div class="profile-card danger-zone">
        <h2 class="section-title">快捷操作</h2>
        <button class="logout-btn" @click="handleLogout">
          <LogOut :size="16" />
          退出登录
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useLoginUserStore } from '@/stores/LoginUser.ts'
import { editUserSelf } from '@/api/userController.ts'
import { message } from 'ant-design-vue'
import { Calendar, LogOut, Loader2, Camera } from '@lucide/vue'
import request from '@/request'

const loginUserStore = useLoginUserStore()
const loginUser = computed(() => loginUserStore.loginUser)
const saving = ref(false)
const uploading = ref(false)
const fileInputRef = ref<HTMLInputElement>()

const editForm = reactive({
  userName: '',
  userAvatar: '',
  userProfile: '',
})

onMounted(async () => {
  await loginUserStore.fetchLoginUser()
  const user = loginUserStore.loginUser
  editForm.userName = user.userName || ''
  editForm.userAvatar = user.userAvatar || ''
  editForm.userProfile = user.userProfile || ''
})

const userInitial = computed(() => {
  const name = loginUserStore.loginUser.userName || loginUserStore.loginUser.userAccount || '?'
  return name.charAt(0).toUpperCase()
})

const avatarStyle = computed(() => {
  if (loginUserStore.loginUser.userAvatar) return {}
  const colors = ['#22C55E', '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B']
  const index = (loginUserStore.loginUser.id || 0) % colors.length
  return { backgroundColor: colors[index] }
})

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const handleSave = async () => {
  saving.value = true
  try {
    const res = await editUserSelf({
      userName: editForm.userName,
      userAvatar: editForm.userAvatar,
      userProfile: editForm.userProfile,
    })
    if (res.data.code === 0) {
      message.success('保存成功')
      await loginUserStore.fetchLoginUser()
    } else {
      message.error(res.data.message || '保存失败')
    }
  } catch {
    message.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const triggerUpload = () => {
  fileInputRef.value?.click()
}

const handleFileChange = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (file.size > 2 * 1024 * 1024) {
    message.error('头像文件不能超过 2MB')
    return
  }
  if (!file.type.startsWith('image/')) {
    message.error('仅支持图片文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const res = await request.post('/file/upload/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      withCredentials: true,
    })
    const data = (res as any)?.data
    if (data?.code === 0 && data?.data) {
      editForm.userAvatar = data.data
      message.success('头像上传成功，点击保存修改生效')
    } else {
      message.error(data?.message || '上传失败')
    }
  } catch (err: unknown) {
    message.error('上传失败，' + (err instanceof Error ? err.message : String(err)))
  } finally {
    uploading.value = false
    input.value = ''
  }
}

const handleLogout = () => {
  loginUserStore.logout()
}
</script>

<style scoped>
.profile-page {
  min-height: calc(100vh - 64px);
  background: var(--color-background);
  padding: var(--space-2xl) var(--space-md);
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.profile-header {
  margin-bottom: var(--space-xl);
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-xl);
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
}

.avatar-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  cursor: pointer;
  position: relative;
}

.avatar-upload-wrapper {
  position: relative;
}

.hidden-input {
  display: none;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s;
}

.avatar-circle:hover .avatar-overlay {
  opacity: 1;
}

.avatar-form-row {
  display: flex;
  gap: 8px;
}

.avatar-form-row .ant-input {
  flex: 1;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initial {
  font-family: var(--font-heading);
  font-size: 32px;
  font-weight: 700;
  color: #fff;
}

.user-meta {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-family: var(--font-heading);
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-xs);
}

.user-tags {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.role-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.role-tag.admin {
  background: rgba(34, 197, 94, 0.15);
  color: var(--color-cta);
  border-color: rgba(34, 197, 94, 0.3);
}

.user-time {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 13px;
  color: var(--color-text-muted);
}

.profile-card {
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

.cta-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: 12px 24px;
  background: var(--color-cta);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 600;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--transition-normal);
  min-width: 140px;
}

.cta-btn:hover:not(:disabled) {
  background: var(--color-cta-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
}

.cta-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.danger-zone {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.danger-zone .section-title {
  margin-bottom: 0;
}

.logout-btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 8px 16px;
  background: transparent;
  color: var(--color-error);
  border: 1px solid var(--color-error);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  font-family: var(--font-body);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.1);
}

@media (max-width: 768px) {
  .avatar-section {
    flex-direction: column;
    text-align: center;
  }

  .user-tags {
    justify-content: center;
  }

  .user-time {
    justify-content: center;
  }

  .danger-zone {
    flex-direction: column;
    gap: var(--space-md);
    align-items: stretch;
  }

  .danger-zone .section-title {
    margin-bottom: 0;
  }

  .logout-btn {
    justify-content: center;
  }
}
</style>
