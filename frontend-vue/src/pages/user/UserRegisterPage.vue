<template>
  <div id="userRegisterPage">
    <h2 class="title">AI应用生成</h2>
    <div class="subtitle">不写一行代码生成完整应用</div>
    <div class="card">
      <h1>注册</h1>
      <a-form :model="formState" autocomplete="off" name="basic" style="margin-top: 24px" @finish="handleSubmit" @finishFailed="onFinishFailed">
        <a-form-item
          :rules="[
            { required: true, message: '请输入账号!' },
            { min: 2, message: '长度不能小于2位' },
            { max: 200, message: '账号长度过长' },
          ]"
          name="userAccount"
        >
          <a-input v-model:value="formState.userAccount" class="formItemBasic" placeholder="请输入账号" />
        </a-form-item>

        <a-form-item
          :rules="[
            { required: true, message: '请输入密码!' },
            { min: 8, message: '长度不能小于8位' },
            { max: 500, message: '长度过长' },
          ]"
          name="userPassword"
        >
          <a-input-password v-model:value="formState.userPassword" class="formItemBasic" placeholder="请输入密码" />
        </a-form-item>

        <a-form-item :rules="[{ required: true, message: '请确认密码!' }, { validator: validator }]" name="checkPassword">
          <a-input-password v-model:value="formState.checkPassword" class="formItemBasic" placeholder="请确认密码" />
        </a-form-item>

        <a-form-item>
          <div class="tip">
            已有账号
            <RouterLink to="/user/login">点击登录</RouterLink>
          </div>
        </a-form-item>
        <a-form-item>
          <a-button class="formItemBasic" html-type="submit" size="large" style="width: 100%" type="primary">注册 </a-button>
        </a-form-item>
      </a-form>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive } from 'vue'
import { userRegister } from '@/api/userController.ts'
import { message } from 'ant-design-vue'
import router from '@/router'

const formState = reactive<API.UserRegisterRequest>({
  userAccount: '',
  userPassword: '',
  checkPassword: '',
})

/**
 * 提交表单
 * @param values
 */
const handleSubmit = async (values: API.UserRegisterRequest) => {
  const res = await userRegister(values)
  if (res.data.code === 0 && res.data.data) {
    message.success('注册成功')
    await router.replace('/user/login')
  }
}

/**
 * 提交失败
 * @param errorInfo
 */
const onFinishFailed = (errorInfo: unknown) => {
  console.log('Failed:', errorInfo)
}

/**
 * 密码验证
 * @param _rule
 * @param value
 */
const validator = (_rule: any, value: string) => {
  if (value && value !== formState.userPassword) {
    return Promise.reject(new Error('两次输入的密码不一致!'))
  }
  return Promise.resolve()
}
</script>

<style scoped>
#userRegisterPage {
  background: url('@/assets/background.png');
  background-size: cover;
  height: 100vh;
}

.tip {
  text-align: right;
}

.title {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 1rem;
}

.subtitle {
  text-align: center;
  font-size: 1.2rem;
  margin-bottom: 2rem;
  color: #666;
}

.card {
  background-color: white;
  border-radius: 10px;
  padding: 36px;
  box-shadow: 0 4px 4px rgba(0, 0, 0, 0.1);
  margin: 0 auto;
  max-width: 400px;
}

.formItemBasic {
  font-size: 1rem;
}
</style>
