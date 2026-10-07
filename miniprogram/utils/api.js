// 网络请求封装：自动携带登录令牌，统一错误处理
const { BASE_URL } = require('../config')

const TOKEN_KEY = 'shanhuo_token'

function getToken() {
  return wx.getStorageSync(TOKEN_KEY) || ''
}

function setToken(token) {
  if (token) wx.setStorageSync(TOKEN_KEY, token)
  else wx.removeStorageSync(TOKEN_KEY)
}

function request(path, method = 'GET', data = null, auth = true) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' }
    const token = getToken()
    if (auth && token) header.Authorization = 'Bearer ' + token
    wx.request({
      url: BASE_URL + path,
      method,
      data: data || undefined,
      header,
      timeout: 120000, // 大模型生成较慢，放宽超时
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          const msg = (res.data && res.data.detail) || `请求失败 (${res.statusCode})`
          reject(new Error(msg))
        }
      },
      fail() {
        reject(new Error('网络请求失败，请确认电脑端服务已启动（python run.py）'))
      },
    })
  })
}

// 图片上传：走 multipart 二进制通道（而非 base64 JSON）
// 原因：微信云托管对「文本请求」限制 100KiB，base64 后的照片会卡在临界点甚至超限；
//       二进制请求额度是 20MiB，用 wx.uploadFile 传文件才稳。
function upload(path, filePath, formData, auth = true) {
  return new Promise((resolve, reject) => {
    const header = {}
    const token = getToken()
    if (auth && token) header.Authorization = 'Bearer ' + token
    wx.uploadFile({
      url: BASE_URL + path,
      filePath,
      name: 'image',
      formData: formData || {},
      header,
      timeout: 120000, // 大模型生成较慢，放宽超时
      success(res) {
        let data = res.data
        if (typeof data === 'string') {
          try { data = JSON.parse(data) } catch (e) { /* 保留原始文本 */ }
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data)
        } else {
          const msg = (data && data.detail) || `请求失败 (${res.statusCode})`
          reject(new Error(msg))
        }
      },
      fail() {
        reject(new Error('网络请求失败，请检查 config.js 里的后端地址与网络连接'))
      },
    })
  })
}

module.exports = {
  BASE_URL,
  getToken,
  setToken,
  request,
  upload,
  recognize: (filePath) => upload('/api/recognize', filePath),
  generate: (info) => request('/api/generate', 'POST', info),
  poster: (filePath, info) => upload('/api/poster', filePath, info),
  tts: (text) => request('/api/tts', 'POST', { text }),
  villages: () => request('/api/villages'),
  guide: (villageId, question = '') => request('/api/guide', 'POST', { village_id: villageId, question }),
  providers: () => request('/api/providers'),
  switchProvider: (providerId) => request('/api/providers/switch', 'POST', { provider_id: providerId }),
  register: (username, password, nickname) =>
    request('/api/auth/register', 'POST', { username, password, nickname: nickname || '' }, false),
  login: (username, password) => request('/api/auth/login', 'POST', { username, password }, false),
  logout: () => request('/api/auth/logout', 'POST', {}),
  me: () => request('/api/auth/me'),
  history: () => request('/api/auth/history'),
  addHistory: (name, title, posterUrl) => request('/api/auth/history', 'POST', { name, title, poster_url: posterUrl }),
  deleteHistory: (id) => request('/api/auth/history/' + id, 'DELETE'),
}
