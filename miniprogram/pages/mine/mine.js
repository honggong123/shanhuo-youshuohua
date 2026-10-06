const api = require('../../utils/api')

Page({
  data: {
    nickname: '',
    username: '',
    engine: null,
    switching: false,
    error: '',
  },

  onShow() {
    if (!api.getToken()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    this.load()
  },

  async load() {
    try {
      const [me, engine] = await Promise.all([api.me(), api.providers()])
      const active = engine.providers.find((p) => p.id === engine.active)
      this.setData({
        nickname: me.user.nickname,
        username: me.user.username,
        engine,
        activeName: active ? active.name : '演示模式',
        error: '',
      })
    } catch (e) {
      // 令牌失效则回到登录页
      api.setToken('')
      wx.reLaunch({ url: '/pages/login/login' })
    }
  },

  async pickProvider(e) {
    const p = e.currentTarget.dataset.p
    if (!p.available || this.data.switching || p.id === this.data.engine.active) return
    this.setData({ switching: true, error: '' })
    try {
      const engine = await api.switchProvider(p.id)
      const active = engine.providers.find((x) => x.id === engine.active)
      this.setData({ engine, activeName: active ? active.name : '演示模式' })
      wx.showToast({ title: '已切换', icon: 'success' })
    } catch (err) {
      this.setData({ error: err.message })
    } finally {
      this.setData({ switching: false })
    }
  },

  logout() {
    wx.showModal({
      title: '退出登录？',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.logout()
        } catch (e) {
          // 本地登出不受影响
        }
        api.setToken('')
        getApp().globalData.userInfo = null
        wx.reLaunch({ url: '/pages/login/login' })
      },
    })
  },
})
