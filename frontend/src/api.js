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

export const api = {
  recognize: (image) => post('/api/recognize', { image }),
  generate: (info) => post('/api/generate', info),
  poster: (payload) => post('/api/poster', payload),
  tts: (text) => post('/api/tts', { text }),
  villages: () => fetch('/api/villages').then((r) => r.json()),
  guide: (village_id, question = '') => post('/api/guide', { village_id, question }),
  providers: () => fetch('/api/providers').then((r) => r.json()),
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
