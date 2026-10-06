const api = require('../../utils/api')

Page({
  data: {
    items: [],
    loading: false,
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
    this.setData({ loading: true, error: '' })
    try {
      const res = await api.history()
      const items = res.items.map((it) => ({
        ...it,
        timeText: this.fmtTime(it.created_at),
        thumb: it.poster_url ? api.BASE_URL + it.poster_url : '',
      }))
      this.setData({ items, loading: false })
    } catch (e) {
      this.setData({ error: e.message, loading: false })
    }
  },

  fmtTime(ts) {
    const d = new Date(ts * 1000)
    const p = (n) => String(n).padStart(2, '0')
    return `${d.getMonth() + 1}月${d.getDate()}日 ${p(d.getHours())}:${p(d.getMinutes())}`
  },

  del(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '删除这条记录？',
      content: '删除后不可恢复',
      confirmText: '删除',
      confirmColor: '#dc2626',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.deleteHistory(id)
          this.setData({ items: this.data.items.filter((x) => x.id !== id) })
          wx.showToast({ title: '已删除', icon: 'success' })
        } catch (err) {
          wx.showToast({ title: err.message, icon: 'none' })
        }
      },
    })
  },
})
