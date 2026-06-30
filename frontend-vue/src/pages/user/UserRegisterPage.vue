<template>
  <AuthShell
    panelEyebrow="Get Started"
    title="注册"
    subtitle="创建账号后，即可在一个连续的 AI 工作流里体验生成、预览与发布。"
    switchPrompt="已经有账号？"
    switchLinkText="返回登录"
    switchTo="/user/login"
    storyTitle="把灵感变成可以上线的作品"
    storyDescription="无论是落地页、作品集还是演示页面，你都可以在同一个创作空间里完成从想法到成品的完整推进。"
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

      <a-form-item
        label="确认密码"
        :rules="[{ required: true, message: '请确认密码' }, { validator: validateCheckPassword }]"
        name="checkPassword"
      >
        <a-input-password v-model:value="formState.checkPassword" placeholder="请再次输入密码" size="large" />
      </a-form-item>

      <a-form-item>
        <button class="auth-submit-btn" type="submit">注册</button>
      </a-form-item>
    </a-form>
  </AuthShell>
</template>

<script lang="ts" setup>
import { reactive } from 'vue'
import { userRegister } from '@/api/userController.ts'
import { message } from 'ant-design-vue'
import type { Rule } from 'ant-design-vue/es/form'
import router from '@/router'
import AuthShell from '@/components/auth/AuthShell.vue'

const formState = reactive<API.UserRegisterRequest>({
  userAccount: '',
  userPassword: '',
  checkPassword: '',
})

const handleSubmit = async (values: API.UserRegisterRequest) => {
  const res = await userRegister(values)
  if (res.data.code === 0 && res.data.data) {
    message.success('注册成功')
    await router.replace('/user/login')
  } else {
    message.error(res.data.message || '注册失败')
  }
}

const onFinishFailed = (errorInfo: unknown) => {
  console.log('Failed:', errorInfo)
}

const validateCheckPassword = (_rule: Rule, value: string) => {
  if (value && value !== formState.userPassword) {
    return Promise.reject(new Error('两次输入的密码不一致'))
  }
  return Promise.resolve()
}
</script>
