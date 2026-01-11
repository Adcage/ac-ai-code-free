<template>
  {{ selectedRow }}
  <div id="userManagePage">
    <a-space style="margin-bottom: 16px">
      <a-form :model="searchParams" layout="inline" @finish="doSearch">
        <a-form-item>
          <a-input v-model:value="searchParams.userAccount" placeholder="搜索用户账号" />
        </a-form-item>
        <a-form-item>
          <a-input v-model:value="searchParams.userName" placeholder="搜索用户名" />
        </a-form-item>
        <a-form-item>
          <a-button html-type="submit" type="primary">搜索</a-button>
        </a-form-item>
      </a-form>
      <a-button v-if="selectedRow.length > 0" danger type="primary" @click="multiDelete">批量删除 </a-button>
      <a-button v-else disabled type="primary">批量删除</a-button>
    </a-space>
    <a-divider />
    <a-table
      :columns="columns"
      :data-source="data"
      :pagination="pagination"
      :row-selection="rowSelection"
      bordered
      row-key="id"
      @change="doTableChange"
    >
      <template #bodyCell="{ column, text, record }">
        <template v-if="column.key === 'userName'">
          <a-input v-if="editableData[record.id]" v-model:value="editableData[record.id].userName" />
          <template v-else>
            {{ text }}
          </template>
        </template>
        <template v-if="column.key === 'userRole'">
          <a-select
            v-if="editableData[record.id]"
            v-model:value="editableData[record.id].userRole"
            style="width: 105px"
          >
            <a-select-option value="admin">管理员</a-select-option>
            <a-select-option value="user">普通用户</a-select-option>
            <a-select-option value="vip"> VIP</a-select-option>
          </a-select>
          <template v-else>
            <a-tag v-if="record.userRole === 'admin'" color="green">管理员</a-tag>
            <a-tag v-else-if="record.userRole === 'user'" color="blue">普通用户</a-tag>
            <a-tag v-else-if="record.userRole === 'vip'" color="pink">会员</a-tag>
            <a-tag v-else color="blue">普通用户</a-tag>
          </template>
        </template>
        <template v-if="column.key === 'userAvatar'">
          <a-image :src="record.userAvatar" :width="48" class="avatar">
            <template #previewMask>
              <EyeOutlined />
            </template>
          </a-image>
        </template>
        <template v-else-if="column.key === 'createTime'">
          {{ dayjs(record?.createTime).format('YYYY-MM-DD HH:mm:ss') }}
        </template>
        <template v-else-if="column.key === 'updateTime'">
          {{ dayjs(record?.updateTime).format('YYYY-MM-DD HH:mm:ss') }}
        </template>
        <template v-else-if="column.key === 'action'">
          <!--当前行不是可编辑状态 -->
          <div v-if="!editableData[record.id]">
            <a-space>
              <a-dropdown trigger="hover">
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="editUser(record)"> 修改</a-menu-item>
                  </a-menu>
                </template>
                <a-button class="optionBtn" type="primary" @click="edit(record)"
                  >编辑
                  <DownOutlined />
                </a-button>
              </a-dropdown>
              <a-popconfirm cancel-text="取消" ok-text="确定" @confirm="handleDelete(record.id)">
                <template #title>
                  确认要删除吗?<br />
                  <p style="color: #666666; font-size: 12px">双击快速删除</p>
                </template>
                <a-button danger type="primary" @dblclick="handleDelete(record.id)">删除</a-button>
              </a-popconfirm>
            </a-space>
          </div>
          <!--当前行进入可编辑状态 -->
          <div v-else>
            <a-space>
              <a-button style="background: #4caf50" type="primary" @click="save(record.id)">保存 </a-button>
              <a-button style="background: #666666" type="primary" @click="cancel(record.id)">取消 </a-button>
            </a-space>
          </div>
        </template>
      </template>
    </a-table>
  </div>
</template>
<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { deleteUser, listUserByPage, updateUser } from '@/api/userController.ts'
import dayjs from 'dayjs'
import type { TableProps } from 'ant-design-vue'
import { message } from 'ant-design-vue'
import { DownOutlined, EyeOutlined } from '@ant-design/icons-vue'
// 表格列表内容
const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
  },
  {
    title: '账号',
    dataIndex: 'userAccount',
    key: 'userAccount',
    ellipsis: true,
  },
  {
    title: '用户名',
    dataIndex: 'userName',
    key: 'userName',
    ellipsis: true,
  },
  {
    title: '用户头像',
    dataIndex: 'userAvatar',
    key: 'userAvatar',
  },
  {
    title: '用户角色',
    dataIndex: 'userRole',
    key: 'userRole',
  },
  {
    title: '创建时间',
    dataIndex: 'createTime',
    key: 'createTime',
  },
  {
    title: '更新时间',
    key: 'updateTime',
    dataIndex: 'updateTime',
  },
  {
    title: '操作',
    key: 'action',
  },
]
//数据
const data = ref<API.User[]>([])
const total = ref(0)
//搜索条件
const searchParams = ref<API.UserQueryRequest>({
  pageNum: 1,
  pageSize: 20,
  userName: '',
  userAccount: '',
})
// 分页
const pagination = computed(() => {
  return {
    current: searchParams.value.pageNum ?? 1,
    pageSize: searchParams.value.pageSize ?? 20,
    total: total.value,
    showSizeChanger: true,
    showTotal: (total: number) => `共 ${total} 条数据`,
  }
})
// 表格多选
const selectedRow = ref<number[]>([])
const rowSelection: TableProps['rowSelection'] = {
  onChange: (selectedRowKeys, selectedRows: API.User[]) => {
    console.log(`selectedRowKeys: ${selectedRowKeys}`, 'selectedRows: ', selectedRows)
    console.log('selectedRowsLen:,', selectedRows.length)
    selectedRow.value = selectedRows.map((item) => item.id) as number[]
  },
}
// 可编辑数据
const editableData = reactive<Record<number, API.User>>({})
/************************函数*************************************************/
// 表格分页变化操作
const doTableChange = (page: any) => {
  searchParams.value.pageNum = page.current
  searchParams.value.pageSize = page.pageSize
  fetchData()
}

// 请求用户数据
const fetchData = async () => {
  const res = await listUserByPage(searchParams.value)
  console.log('fetch数据', res)
  data.value = res.data?.data?.records || []
  total.value = res.data?.data?.totalRow || 0
}
//搜索
const doSearch = () => {
  //重置页码
  searchParams.value.pageNum = 1
  //重新请求数据
  fetchData()
}
// 删除用户
const handleDelete = async (id: number) => {
  if (!id) {
    message.error('请选择要删除的用户,没有id')
    return
  }
  // 删除请求发送
  const res = await deleteUser({ id })
  if (res.data.code === 0) {
    message.success('删除成功')
    data.value.splice(
      data.value.findIndex((item) => item.id === id),
      1,
    )
  } else {
    message.error('删除失败' + res.data.message)
  }
}
// 修改用户信息
const editUser = async (rowData: API.User) => {
  //TODO 展开修改用户信息弹窗
}

// 批量删除
const multiDelete = async () => {
  //TODO 批量删除用户
}
// 行编辑操作
const edit = (rowData: API.User) => {
  editableData[rowData.id ?? 0] = JSON.parse(JSON.stringify(rowData))
}
const save = async (id: number) => {
  const res = await updateUser(editableData[id])
  if (res.data.code === 0) {
    message.success('编辑成功')
    data.value.splice(
      data.value.findIndex((item) => item.id === id),
      1,
      editableData[id],
    )
    delete editableData[id]
  } else {
    message.error('修改失败' + res.data.message)
  }
}
const cancel = (id: number) => {
  delete editableData[id]
}
// 页面加载时执行
onMounted(() => {
  fetchData()
})
</script>
<style scoped>
#userManagePage {
  margin: 0 100px;
  width: 1500px;
}

.selectOpt {
  margin: 10px !important;
  background: red !important;
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}
</style>
