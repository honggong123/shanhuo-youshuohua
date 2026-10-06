const api = require('../../utils/api')

Page({
  data: {
    photoPath: '',
    rec: null,
    recLoading: false,
    gen: null,
    posterUrl: '',
    audioUrl: '',
    playing: false,
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
        const raw = res.tempFiles[0].tempFilePath
        // 压缩后再上传：相机原图动辄好几 MB，base64 后请求又慢又容易失败
        wx.compressImage({
          src: raw,
          quality: 60,
          success: (c) => this.setPhoto(c.tempFilePath),
          fail: () => this.setPhoto(raw),
        })
      },
    })
  },

  setPhoto(path) {
    this.stopAudio()
    this.setData({
      photoPath: path,
      rec: null,
      gen: null,
      posterUrl: '',
      audioUrl: '',
      error: '',
      playing: false,
    })
  },

  stopAudio() {
    if (this.audio && this.data.playing) this.audio.stop()
    if (this.data.playing) this.setData({ playing: false })
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
    this.stopAudio()
    this.setData({ copyLoading: true, posterLoading: true, audioLoading: true, ttsError: '', error: '', playing: false })

    const b64 = await this.readFileB64(this.data.photoPath).catch(() => '')

    const [copySettled, posterSettled] = await Promise.allSettled([
      api.generate(info),
      api.poster({ image: b64, name: rec.name, origin: rec.origin, tagline: '' }),
    ])

    if (copySettled.status === 'fulfilled') {
      this.setData({ gen: copySettled.value })
    } else {
      this.setData({ error: `文案生成失败：${copySettled.reason.message}` })
    }

    if (posterSettled.status === 'fulfilled') {
      // 海报地址需拼上服务器前缀，小程序才能加载
      this.setData({ posterUrl: api.BASE_URL + posterSettled.value.url })
    } else {
      this.setData({ error: `海报生成失败：${posterSettled.reason.message}` })
    }

    const genResult = this.data.gen
    if (genResult) {
      try {
        const t = await api.tts(`${genResult.title}。${genResult.story}`)
        this.setData({ audioUrl: t.url })
      } catch (e) {
        this.setData({ ttsError: `语音生成失败：${e.message}` })
      }
      // 登录用户自动存档（历史里存相对路径）
      api
        .addHistory(rec.name, genResult.title, posterSettled.status === 'fulfilled' ? posterSettled.value.url : '')
        .catch(() => {})
    }
    this.setData({ copyLoading: false, posterLoading: false, audioLoading: false })
  },

  onShareAppMessage() {
    return {
      title: '山货有话说 · AI 让每一份山货开口说话',
      path: '/pages/index/index',
    }
  },

  // ---- 语音播放 / 暂停 ----
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

  // ---- 海报保存到相册 ----
  savePoster() {
    const url = this.data.posterUrl
    if (!url) return
    wx.downloadFile({
      url,
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
