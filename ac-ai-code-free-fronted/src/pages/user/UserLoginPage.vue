<template>
  <div id="userLoginPage">
    <h2 class="title">AI应用生成</h2>
    <div class="subtitle">不写一行代码生成完整应用</div>
    <div class="card">
      <h1>登录</h1>
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
            // { pattern: /^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d]{8,}$/, message: '密码必须包含字母和数字' },
          ]"
          name="userPassword"
        >
          <a-input-password v-model:value="formState.userPassword" class="formItemBasic" placeholder="请输入密码" />
        </a-form-item>

        <a-form-item>
          <div class="tip">
            没有账号
            <RouterLink to="/user/register">点击注册</RouterLink>
          </div>
        </a-form-item>
        <a-form-item>
          <a-button class="formItemBasic" html-type="submit" size="large" style="width: 100%" type="primary">登录 </a-button>
        </a-form-item>
      </a-form>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive } from 'vue'
import { userLogin } from '@/api/userController.ts'
import { useLoginUserStore } from '@/stores/LoginUser.ts'
import { message } from 'ant-design-vue'
import router from '@/router'
import { useRoute } from 'vue-router'

const formState = reactive<API.UserLoginRequest>({
  userAccount: '',
  userPassword: '',
})
const LoginUserStore = useLoginUserStore()
const route = useRoute()

/**
 * 提交表单
 * @param values
 */
const handleSubmit = async (values: API.UserLoginRequest) => {
  const res = await userLogin(values)
  if (res.data.code === 0 && res.data.data) {
    LoginUserStore.setLoginUser(res.data.data)
    message.success('登录成功')
    await router.replace(route.query.redirect as string)
  } else {
    message.error(res.data.message)
  }
}

/**
 * 提交失败
 * @param errorInfo
 */
const onFinishFailed = (errorInfo: unknown) => {
  // 使用 unknown 作为临时类型修复
  console.log('Failed:', errorInfo)
}
</script>

<style scoped>
#userLoginPage {
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
