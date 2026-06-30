<template>
  <AuthShell
    panelEyebrow="Welcome Back"
    title="登录"
    subtitle="回到你的创作台，在连续的 AI 工作流里继续推进页面、内容与发布。"
    switchPrompt="还没有账号？"
    switchLinkText="创建新账号"
    switchTo="/user/register"
    storyTitle="开始你的下一次创作"
    storyDescription="从提示词、页面预览到一键部署，原象把完整创作流程留在同一个工作台里，让灵感可以持续推进而不是反复中断。"
  >
    <a-form
      :model="formState"
      autocomplete="off"
      layout="vertical"
      @finish="handleSubmit"
      @finishFailed="onFinishFailed"
    >
      <a-form-item
        label="账号"
        :rules="[
          { required: true, message: '请输入账号' },
          { min: 2, message: '长度不能小于2位' },
          { max: 200, message: '账号长度过长' },
        ]"
        name="userAccount"
      >
        <a-input v-model:value="formState.userAccount" placeholder="请输入账号" size="large" />
      </a-form-item>

      <a-form-item
        label="密码"
        :rules="[
          { required: true, message: '请输入密码' },
          { min: 8, message: '长度不能小于8位' },
          { max: 500, message: '长度过长' },
        ]"
        name="userPassword"
      >
        <a-input-password v-model:value="formState.userPassword" placeholder="请输入密码" size="large" />
      </a-form-item>

      <a-form-item>
        <button class="auth-submit-btn" type="submit">登录</button>
      </a-form-item>
    </a-form>
  </AuthShell>
</template>

<script lang="ts" setup>
import { reactive } from 'vue'
import { userLogin } from '@/api/userController.ts'
import { useLoginUserStore } from '@/stores/LoginUser.ts'
import { message } from 'ant-design-vue'
import router from '@/router'
import { useRoute } from 'vue-router'
import AuthShell from '@/components/auth/AuthShell.vue'

const formState = reactive<API.UserLoginRequest>({
  userAccount: '',
  userPassword: '',
})
const LoginUserStore = useLoginUserStore()
const route = useRoute()

const handleSubmit = async (values: API.UserLoginRequest) => {
  const res = await userLogin(values)
  if (res.data.code === 0 && res.data.data) {
    LoginUserStore.setLoginUser(res.data.data)
    message.success('登录成功')
    const redirect = route.query.redirect as string
    if (redirect) {
      await router.replace(redirect)
    } else if (res.data.data.userRole === 'admin') {
      await router.replace('/admin')
    } else {
      await router.replace('/')
    }
  } else {
    message.error(res.data.message || '登录失败')
  }
}

const onFinishFailed = (errorInfo: unknown) => {
  console.log('Failed:', errorInfo)
}
</script>
