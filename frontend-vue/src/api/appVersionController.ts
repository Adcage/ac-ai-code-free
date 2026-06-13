// @ts-ignore
/* eslint-disable */
import request from '@/request'

/** 获取应用版本列表 GET /app-version/list */
export async function listAppVersions(
  params: { appId: number; limit?: number },
  options?: { [key: string]: any },
) {
  return request<API.BaseResponseListAppVersionVO>('/app-version/list', {
    method: 'GET',
    params: {
      ...params,
    },
    ...(options || {}),
  })
}
