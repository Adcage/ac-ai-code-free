// @ts-ignore
/* eslint-disable */
import request from '@/request'

/** 此处后端没有提供注释 POST /file/upload/avatar */
export async function uploadAvatar(body: {}, options?: { [key: string]: any }) {
  return request<API.BaseResponseString>('/file/upload/avatar', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    data: body,
    ...(options || {}),
  })
}
