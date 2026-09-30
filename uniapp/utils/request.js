import { baseURL } from './config.js'

function token() {
  return uni.getStorageSync('access') || ''
}

export function clearAuth() {
  uni.removeStorageSync('access')
  uni.removeStorageSync('refresh')
  uni.removeStorageSync('user')
}

function refreshToken() {
  const refresh = uni.getStorageSync('refresh')
  if (!refresh) return Promise.resolve(false)
  return new Promise((resolve) => {
    uni.request({
      url: baseURL + '/api/auth/refresh/',
      method: 'POST',
      data: { refresh },
      success: (res) => {
        const body = res.data || {}
        if (res.statusCode === 200 && body.code === 0 && body.data && body.data.access) {
          uni.setStorageSync('access', body.data.access)
          resolve(true)
        } else {
          resolve(false)
        }
      },
      fail: () => resolve(false)
    })
  })
}

export function request(options, retried) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: baseURL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: Object.assign({
        'Content-Type': 'application/json',
        Authorization: token() ? 'Bearer ' + token() : ''
      }, options.header || {}),
      success: (res) => {
        const body = res.data || {}
        if (res.statusCode === 401 && !retried && options.url.indexOf('/api/auth/') !== 0) {
          refreshToken().then((ok) => {
            if (!ok) {
              clearAuth()
              uni.reLaunch({ url: '/pages/login/login' })
              reject(body)
              return
            }
            request(options, true).then(resolve, reject)
          })
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300 && body.code === 0) {
          resolve(body.data)
          return
        }
        const message = body.message || '请求失败'
        if (!options.silent) uni.showToast({ title: message, icon: 'none' })
        reject(body)
      },
      fail: () => {
        if (!options.silent) uni.showToast({ title: '网络异常', icon: 'none' })
        reject(new Error('network'))
      }
    })
  })
}

export function upload(options) {
  return new Promise((resolve, reject) => {
    const task = uni.uploadFile({
      url: baseURL + options.url,
      filePath: options.filePath,
      name: 'file',
      formData: options.formData || {},
      header: { Authorization: token() ? 'Bearer ' + token() : '' },
      success: (res) => {
        let body = {}
        try {
          body = JSON.parse(res.data)
        } catch (error) {
          body = {}
        }
        if (res.statusCode >= 200 && res.statusCode < 300 && body.code === 0) {
          resolve(body.data)
          return
        }
        uni.showToast({ title: body.message || '上传失败', icon: 'none' })
        reject(body)
      },
      fail: () => {
        uni.showToast({ title: '上传失败', icon: 'none' })
        reject(new Error('upload'))
      }
    })
    if (task && task.onProgressUpdate && options.onProgress) {
      task.onProgressUpdate((event) => options.onProgress(event.progress || 0))
    }
  })
}

export function saveSession(data) {
  uni.setStorageSync('access', data.access)
  uni.setStorageSync('refresh', data.refresh)
  uni.setStorageSync('user', data.user)
}

export function currentUser() {
  return uni.getStorageSync('user') || {}
}

export function hasPerm(code) {
  const permissions = currentUser().permissions || []
  return permissions.indexOf(code) >= 0
}

export function ensureLogin() {
  if (!uni.getStorageSync('access')) {
    uni.reLaunch({ url: '/pages/login/login' })
    return false
  }
  return true
}

export function compressImage(path) {
  return new Promise((resolve) => {
    uni.compressImage({
      src: path,
      quality: 80,
      success: (res) => resolve(res.tempFilePath || path),
      fail: () => resolve(path)
    })
  })
}
