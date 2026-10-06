const api = require('../../utils/api')

Page({
  data: {
    villages: [],
    provinces: [],
    provinceTabs: ['全部'],
    selectedProvince: '全部',
    current: '',
    story: '',
    audioUrl: '',
    playing: false,
    question: '',
    loadingStory: false,
    loadingAudio: false,
    demo: false,
    error: '',
  },

  audio: null,

  onShow() {
    if (!api.getToken()) {
      wx.reLaunch({ url: '/pages/login/login' })
      return
    }
    if (!this.data.villages.length) this.loadVillages()
  },

  onUnload() {
    if (this.audio) this.audio.destroy()
  },

  async loadVillages() {
    try {
      const villages = await api.villages()
      const provinces = [...new Set(villages.map((v) => v.province))]
      this.setData({
        villages,
        provinces,
        provinceTabs: ['全部', ...provinces],
        current: villages[0] ? villages[0].id : '',
      })
    } catch (e) {
      this.setData({ error: e.message })
    }
  },

  villagesOf(province) {
    const { villages } = this.data
    if (province === '全部') return villages
    return villages.filter((v) => v.province === province)
  },

  pickProvince(e) {
    const p = e.currentTarget.dataset.p
    const rest = this.villagesOf(p)
    const stillThere = rest.some((v) => v.id === this.data.current)
    this.setData({
      selectedProvince: p,
      current: stillThere ? this.data.current : rest[0] ? rest[0].id : '',
    })
  },

  pickVillage(e) {
    this.setData({ current: e.currentTarget.dataset.id })
  },

  async tell() {
    if (!this.data.current) return
    this.setData({ loadingStory: true, error: '', audioUrl: '', playing: false })
    try {
      const res = await api.guide(this.data.current)
      this.setData({ story: res.story, demo: res.demo, loadingAudio: true, loadingStory: false })
      try {
        const t = await api.tts(res.story)
        this.setData({ audioUrl: t.url, loadingAudio: false })
      } catch (e) {
        this.setData({ loadingAudio: false, error: `语音生成失败：${e.message}` })
      }
    } catch (e) {
      this.setData({ error: e.message, loadingStory: false })
    }
  },

  async ask() {
    const q = this.data.question.trim()
    if (!q) return
    this.setData({ loadingStory: true, error: '', audioUrl: '', playing: false })
    try {
      const res = await api.guide(this.data.current, q)
      this.setData({ story: res.story, demo: res.demo, loadingStory: false })
    } catch (e) {
      this.setData({ error: e.message, loadingStory: false })
    }
  },

  playAudio() {
    if (!this.data.audioUrl) return
    if (!this.audio) {
      this.audio = wx.createInnerAudioContext()
      this.audio.onEnded(() => this.setData({ playing: false }))
      this.audio.onError(() => {
        this.setData({ playing: false })
        wx.showToast({ title: '播放失败', icon: 'none' })
      })
    }
    const full = api.BASE_URL + this.data.audioUrl
    if (this.audio.src !== full) {
      this.audio.src = full
      this.audio.seek(0)
    }
    if (this.data.playing) {
      this.audio.pause()
      this.setData({ playing: false })
    } else {
      this.audio.play()
      this.setData({ playing: true })
    }
  },

  onInput(e) {
    this.setData({ question: e.detail.value })
  },
})
