const TOKEN_KEY = 'shanhuo_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

function authHeaders() {
  const h = { 'Content-Type': 'application/json' }
  const t = getToken()
  if (t) h.Authorization = 'Bearer ' + t
  return h
}

async function post(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `请求失败 (${res.status})`)
  return data
}

async function authedGet(url) {
  const res = await fetch(url, { headers: authHeaders() })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `请求失败 (${res.status})`)
  return data
}

// dataURL -> Blob：图片走 multipart 二进制通道，避免 base64 撑大请求体
function dataUrlToBlob(dataUrl) {
  const [head, body] = dataUrl.split(',')
  const mime = (head.match(/data:([^;]+)/) || [])[1] || 'image/jpeg'
  const bin = atob(body)
  const bytes = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i)
  return new Blob([bytes], { type: mime })
}

// multipart/form-data 上传：Blob 作为文件字段，其余作为普通文本字段。
// 不手动设置 Content-Type，交给浏览器带上 multipart boundary。
async function uploadForm(url, fields) {
  const fd = new FormData()
  for (const [k, v] of Object.entries(fields)) {
    if (v == null || v === '') continue
    fd.append(k, v instanceof Blob ? v : String(v))
  }
  const headers = {}
  const t = getToken()
  if (t) headers.Authorization = 'Bearer ' + t
  const res = await fetch(url, { method: 'POST', headers, body: fd })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `请求失败 (${res.status})`)
  return data
}

export const api = {
  recognize: (imageDataUrl) => uploadForm('/api/recognize', { image: dataUrlToBlob(imageDataUrl) }),
  generate: (info) => post('/api/generate', info),
  poster: ({ image, name, tagline = '', origin = '' }) =>
    uploadForm('/api/poster', { image: dataUrlToBlob(image), name, tagline, origin }),
  tts: (text) => post('/api/tts', { text }),
  villages: () => fetch('/api/villages').then((r) => r.json()),
  guide: (village_id, question = '') => post('/api/guide', { village_id, question }),
  providers: () => authedGet('/api/providers'),
  switchProvider: (provider_id) => post('/api/providers/switch', { provider_id }),
  connectProvider: (provider_id, api_key) => post('/api/providers/connect', { provider_id, api_key }),

  register: (username, password, nickname) => post('/api/auth/register', { username, password, nickname }),
  login: (username, password) => post('/api/auth/login', { username, password }),
  logout: () => post('/api/auth/logout', {}),
  me: () => authedGet('/api/auth/me'),
  history: () => authedGet('/api/auth/history'),
  addHistory: (name, title, poster_url) => post('/api/auth/history', { name, title, poster_url }),
  deleteHistory: (id) =>
    fetch(`/api/auth/history/${id}`, { method: 'DELETE', headers: authHeaders() }).then((r) => {
      if (!r.ok) throw new Error(`删除失败 (${r.status})`)
      return r.json()
    }),
}
