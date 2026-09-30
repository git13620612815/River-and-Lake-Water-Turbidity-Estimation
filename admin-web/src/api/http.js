import axios from 'axios'

export const apiBase = 'http://127.0.0.1:8000'

const http = axios.create({ baseURL: apiBase })

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && body.code === 0) return body.data
    return Promise.reject(new Error((body && body.message) || '请求失败'))
  },
  async (error) => {
    const status = error.response && error.response.status
    const body = error.response && error.response.data
    const original = error.config || {}
    if (status === 401 && !original._retried && !String(original.url || '').includes('/auth/')) {
      original._retried = true
      const refresh = localStorage.getItem('admin_refresh')
      if (refresh) {
        try {
          const refreshed = await axios.post(`${apiBase}/api/auth/refresh/`, { refresh })
          if (refreshed.data && refreshed.data.code === 0) {
            localStorage.setItem('admin_access', refreshed.data.data.access)
            original.headers.Authorization = `Bearer ${refreshed.data.data.access}`
            return http(original)
          }
        } catch (refreshError) {
          /* 继续退出登录 */
        }
      }
      localStorage.removeItem('admin_access')
      localStorage.removeItem('admin_refresh')
      localStorage.removeItem('admin_user')
      if (location.pathname !== '/login') location.href = '/login'
    }
    const message = (body && body.message) || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export function mediaUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return apiBase + path
}

export const LEVELS = [
  { code: 'clear', name: '清澈', color: '#0284c7' },
  { code: 'slight', name: '轻度浑浊', color: '#0d9488' },
  { code: 'moderate', name: '中度浑浊', color: '#ea580c' },
  { code: 'severe', name: '重度浑浊', color: '#dc2626' }
]

export function currentUser() {
  try {
    return JSON.parse(localStorage.getItem('admin_user') || '{}')
  } catch (error) {
    return {}
  }
}

export function hasPerm(code) {
  const permissions = currentUser().permissions || []
  return permissions.includes(code)
}

export default http
