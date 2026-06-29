<template>
  <div class="settings-page">
    <div class="settings-container">
      <div class="page-title-block">
        <div class="accent-bar"></div>
        <div>
          <h1 class="page-title">账号设置</h1>
        </div>
      </div>

      <div class="settings-layout">
        <!-- 左栏：头像 + 用户信息 -->
        <div class="profile-sidebar">
          <UserAvatar :user="loginUserStore.loginUser" :size="120" class="profile-avatar" />
          <div class="profile-name">{{ loginUserStore.loginUser.userName || '未命名' }}</div>
          <div class="profile-bio">{{ editForm.userProfile || '还没有简介' }}</div>
        </div>

        <!-- 右栏：表单 -->
        <div class="settings-form">
          <div class="form-field">
            <label>昵称</label>
            <a-input v-model:value="editForm.userName" placeholder="输入昵称" :maxlength="256" :bordered="false" />
          </div>
          <div class="form-field">
            <label>用户头像 URL</label>
            <a-input v-model:value="editForm.userAvatar" placeholder="输入头像 URL" :bordered="false" />
          </div>
          <div class="form-field">
            <label>个人简介</label>
            <a-textarea
              v-model:value="editForm.userProfile"
              placeholder="写点什么..."
              :maxlength="1024"
              :rows="2"
              :bordered="false"
              class="profile-textarea"
            />
          </div>

          <div class="security-section">
            <div class="security-item">
              <span>修改密码</span>
              <span class="coming-soon">即将推出</span>
            </div>
            <div class="security-item">
              <span>绑定邮箱</span>
              <span class="coming-soon">即将推出</span>
            </div>
            <div class="security-item">
              <span>双重验证</span>
              <span class="coming-soon">即将推出</span>
            </div>
          </div>

          <button class="btn-save" :class="{ saving: saving }" :disabled="saving" @click="handleSave">
            {{ saving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useLoginUserStore } from '@/stores/LoginUser.ts'
import { editUserSelf } from '@/api/userController'
import UserAvatar from '@/components/UserAvatar.vue'

const loginUserStore = useLoginUserStore()
const saving = ref(false)

const editForm = ref({
  userName: '',
  userAvatar: '',
  userProfile: '',
})

onMounted(() => {
  const user = loginUserStore.loginUser
  editForm.value = {
    userName: user.userName || '',
    userAvatar: user.userAvatar || '',
    userProfile: user.userProfile || '',
  }
})

const handleSave = async () => {
  saving.value = true
  try {
    const res = await editUserSelf({
      userName: editForm.value.userName,
      userAvatar: editForm.value.userAvatar,
      userProfile: editForm.value.userProfile,
    })
    if (res.data.code === 0) {
      message.success('保存成功')
      await loginUserStore.fetchLoginUser()
    } else {
      message.error('保存失败：' + (res.data.message || '未知错误'))
    }
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.settings-page {
  min-height: calc(100vh - 64px);
  background: var(--color-background);
}

.settings-container {
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

/* ── 两栏布局：30% 资料 + 65% 表单 ── */
.settings-layout {
  display: grid;
  grid-template-columns: 30% 65%;
  gap: 5%;
  padding-bottom: var(--space-section);
}

/* ── 左栏：头像 120px + 用户信息 ── */
.profile-sidebar {
  text-align: center;
  padding-top: 8px;
}

.profile-avatar {
  margin: 0 auto 20px;
  display: block;
}

.profile-name {
  font-family: var(--font-heading);
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--color-text);
}

.profile-bio {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-lg);
  line-height: 1.6;
}

/* ── 右栏：表单字段 ── */
.form-field {
  margin-bottom: var(--space-field);
}

.form-field label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--color-text-muted);
  margin-bottom: 12px;
}

/* Ant 输入框改为底线样式 */
.form-field :deep(.ant-input),
.form-field :deep(.ant-input-affix-wrapper) {
  padding: 12px 0;
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text);
  background: none !important;
  border: none !important;
  border-bottom: 1px solid var(--color-border) !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  transition: border-color var(--transition-fast);
}

.form-field :deep(.ant-input:focus),
.form-field :deep(.ant-input-focused),
.form-field :deep(.ant-input-affix-wrapper-focused) {
  border-bottom-color: var(--color-cta) !important;
  box-shadow: none !important;
}

.form-field :deep(.ant-input::placeholder) {
  color: var(--color-text-muted);
}

.profile-textarea :deep(.ant-input) {
  border-bottom: 1px solid var(--color-border) !important;
  resize: none;
}

/* ── 账户安全 section ── */
.security-section {
  margin-top: var(--space-block);
  padding-top: var(--space-xl);
  border-top: 1px solid var(--color-border);
}

.security-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0;
  border-bottom: 1px solid var(--color-border);
}

.security-item:last-child {
  border-bottom: none;
}

.security-item span {
  font-size: 16px;
  color: var(--color-text);
}

.security-item .coming-soon {
  font-size: 13px;
  color: var(--color-cta);
  font-weight: 500;
}

/* ── 文字保存按钮（带下划线动画） ── */
.btn-save {
  margin-top: var(--space-xl);
  padding: 0;
  padding-bottom: 2px;
  font-family: var(--font-body);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-cta);
  background: none;
  border: none;
  cursor: pointer;
  position: relative;
  transition: opacity var(--transition-fast);
}

.btn-save::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--color-cta);
  transition: width var(--transition-slow);
}

.btn-save:hover:not(:disabled)::after {
  width: 100%;
}

.btn-save.saving,
.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }

  .profile-sidebar {
    margin-bottom: var(--space-block);
  }
}

@media (max-width: 640px) {
  .settings-container {
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
