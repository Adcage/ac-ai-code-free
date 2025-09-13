// @ts-ignore
/* eslint-disable */
import request from '@/request'

/** 此处后端没有提供注释 GET /health/check */
export async function check(options?: { [key: string]: any }) {
  return request<string>('/health/check', {
    method: 'GET',
    ...(options || {}),
  })
}

/** 此处后端没有提供注释 GET /health/status */
export async function status(options?: { [key: string]: any }) {
  return request<string>('/health/status', {
    method: 'GET',
    ...(options || {}),
  })
}
