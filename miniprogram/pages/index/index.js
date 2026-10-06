const api = require('../../utils/api')

Page({
  data: {
    photoPath: '',
    rec: null,
    recLoading: false,
    gen: null,
    posterUrl: '',
    audioUrl: '',
    ttsError: '',
    tab: 'copy',
    error: '',
    copyLoading: false,
    posterLoading: false,
    audioLoading: false,
  },

  audio: null,

  onShow() {
    if (!api.getToken()) {
      wx.reLaunch({ url: '/pages/login/login' })
    }
  },

  onUnload() {
    if (this.audio) this.audio.destroy()
  },

  // ---- 第一步：拍照 / 选图 ----
  chooseImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const path = res.tempFiles[0].tempFilePath
        this.setData({ photoPath: path, rec: null, gen: null, posterUrl: '', audioUrl: '', error: '' })
      },
    })
  },

  readFileB64(path) {
    return new Promise((resolve, reject) => {
      wx.getFileSystemManager().readFile({
        filePath: path,
        encoding: 'base64',
        success: (res) => resolve(res.data),
        fail: () => reject(new Error('图片读取失败')),
      })
    })
  },

  // ---- 第二步：AI 识别 ----
  async recognize() {
    this.setData({ recLoading: true, error: '' })
    try {
      const b64 = await this.readFileB64(this.data.photoPath)
      const rec = await api.recognize(b64)
      this.setData({ rec, recLoading: false })
    } catch (e) {
      this.setData({ error: e.message, recLoading: false })
    }
  },

  switchTab(e) {
    this.setData({ tab: e.currentTarget.dataset.tab })
  },

  // ---- 第三步：一键生成四件套 ----
  async generateAll() {
    const { rec } = this.data
    const info = {
      name: rec.name,
      category: rec.category,
      origin: rec.origin,
      highlights: rec.highlights,
    }
    this.setData({ copyLoading: true, posterLoading: true, audioLoading: true, ttsError: '', error: '' })

    const b64 = await this.readFileB64(this.data.photoPath).catch(() => '')

    try {
      const [gen] = await Promise.allSettled([
        api.generate(info).then((g) => this.setData({ gen: g })),
        api
          .poster({ image: b64, name: rec.name, origin: rec.origin, tagline: '' })
          .then((p) => this.setData({ posterUrl: p.url })),
      ])
      const genResult = this.data.gen
      if (!genResult) {
        this.setData({ copyLoading: false, posterLoading: false, audioLoading: false })
        return
      }
      // 语音依赖文案结果
      try {
        const t = await api.tts(`${genResult.title}。${genResult.story}`)
        this.setData({ audioUrl: t.url })
      } catch (e) {
        this.setData({ ttsError: `语音生成失败：${e.message}` })
      } finally {
        this.setData({ copyLoading: false, posterLoading: false, audioLoading: false })
      }
      // 登录用户自动存档
      api
        .addHistory(rec.name, genResult.title, this.data.posterUrl || '')
        .catch(() => {})
    } catch (e) {
      this.setData({ error: e.message, copyLoading: false, posterLoading: false, audioLoading: false })
    }
  },

  // ---- 语音播放 ----
  playAudio() {
    if (!this.data.audioUrl) return
    if (!this.audio) this.audio = wx.createInnerAudioContext()
    this.audio.src = api.BASE_URL + this.data.audioUrl
    this.audio.play()
  },

  // ---- 海报保存到相册 ----
  savePoster() {
    const url = this.data.posterUrl
    if (!url) return
    wx.downloadFile({
      url: api.BASE_URL + url,
      success: (res) => {
        wx.saveImageToPhotosAlbum({
          filePath: res.tempFilePath,
          success: () => wx.showToast({ title: '已保存到相册', icon: 'success' }),
          fail: () => wx.showToast({ title: '保存失败，请授权相册权限', icon: 'none' }),
        })
      },
      fail: () => wx.showToast({ title: '下载失败', icon: 'none' }),
    })
  },
})
