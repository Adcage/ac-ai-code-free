import { ref } from 'vue'
import { defineStore } from 'pinia'
import { getLoginUser, userLogout } from '@/api/userController.ts'
import { message } from 'ant-design-vue'
import router from '@/router'

export const useLoginUserStore = defineStore('loginUser', () => {
  // 未登录状态常量
  const NOT_LOGIN_USER = {
    userName: '未登录',
  }
  // 登录状态存储
  const loginUser = ref<API.LoginUserVO>(NOT_LOGIN_USER)

  // 从后端获取用户登录信息
  async function fetchLoginUser() {
    const res = await getLoginUser()
    if (res.data.code === 0 && res.data.data) {
      loginUser.value = res.data.data
    }
  }

  // 更新设置用户登录信息
  function setLoginUser(newUser: API.LoginUserVO) {
    loginUser.value = newUser
  }

  //登出
  async function logout() {
    const res = await userLogout()
    if (res.data.code === 0) {
      setLoginUser(NOT_LOGIN_USER)
      message.success('退出成功')
      await router.replace('/')
    } else {
      message.error(res.data.message)
    }
  }

  return {
    loginUser,
    fetchLoginUser,
    setLoginUser,
    logout,
  }
})
