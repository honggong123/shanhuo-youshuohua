const api = require('../../utils/api')

Page({
  data: {
    tab: 'login',
    username: '',
    password: '',
    nickname: '',
    busy: false,
    error: '',
  },

  onShow() {
    // 已有令牌则直接进入主应用
    if (api.getToken()) {
      api.me()
        .then(() => wx.reLaunch({ url: '/pages/index/index' }))
        .catch(() => api.setToken(''))
    }
  },

  setTab(e) {
    this.setData({ tab: e.currentTarget.dataset.tab, error: '' })
  },

  onInput(e) {
    this.setData({ [e.currentTarget.dataset.field]: e.detail.value })
  },

  async submit() {
    const { tab, username, password, nickname } = this.data
    if (!username.trim() || !password) {
      this.setData({ error: '请输入用户名和密码' })
      return
    }
    this.setData({ busy: true, error: '' })
    try {
      const res = tab === 'register'
        ? await api.register(username.trim(), password, nickname)
        : await api.login(username.trim(), password)
      api.setToken(res.token)
      getApp().globalData.userInfo = res.user
      wx.reLaunch({ url: '/pages/index/index' })
    } catch (e) {
      this.setData({ error: e.message })
    } finally {
      this.setData({ busy: false })
    }
  },
})
