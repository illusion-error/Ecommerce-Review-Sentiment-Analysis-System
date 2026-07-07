// frontend/src/api/index.js
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const request = axios.create({
  timeout: 60000, // 批量分析可能慢，超时设长一点（60秒）
})

// 响应拦截器：统一处理错误（完成 A-07 的一部分）
request.interceptors.response.use(
  (response) => {
    return response.data; // 直接返回后端 data，少写一层 .data
  },
  (error) => {
    ElMessage.error(error.response?.data?.message || '服务器开小差了，请稍后再试')
    return Promise.reject(error)
  }
)

// 导出具体的接口函数
// 1. 单条分析接口 (B-03)
export const analyzeSingle = (text) => {
  return request.post('/api/sentiment/single', { text })
}

// 2. 获取历史记录 (B-05)
export const getHistory = (params) => {
  return request.get('/api/history', { params })
}

// 3. 获取统计数据 (B-06)
export const getStatistics = () => {
  return request.get('/api/statistics/summary')
}

// 注意：批量上传(B-04)和导出(B-07)我们在组件里单独写