// @ts-ignore
/* eslint-disable */
import request from '@/request'

/** 此处后端没有提供注释 GET /app-version/list */
export async function listVersions(
  // 叠加生成的Param类型 (非body参数swagger默认没有生成对象)
  params: API.listVersionsParams,
  options?: { [key: string]: any }
) {
  return request<API.BaseResponseListAppVersionVO>('/app-version/list', {
    method: 'GET',
    params: {
      // limit has a default value: 20
      limit: '20',
      ...params,
    },
    ...(options || {}),
  })
}
