<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, getToken, setToken } from './api'
import UploadPanel from './components/UploadPanel.vue'
import ResultsPanel from './components/ResultsPanel.vue'
import GuidePanel from './components/GuidePanel.vue'
import ConnectModal from './components/ConnectModal.vue'
import LoginScreen from './components/LoginScreen.vue'
import HistoryPanel from './components/HistoryPanel.vue'

const photo = ref('')
const rec = ref(null)
const gen = ref(null)
const poster = ref(null)
const audioUrl = ref('')
const ttsError = ref('')
const recError = ref('')
const engine = ref(null)
const switching = ref(false)
const connectOpen = ref(false)
const user = ref(null)
const booting = ref(true)
const histTick = ref(0)
const loading = reactive({ rec: false, copy: false, poster: false, audio: false })

const demoMode = computed(() => engine.value?.demo ?? false)

onMounted(async () => {
  try {
    engine.value = await api.providers()
  } catch {
    engine.value = null
  }
  // 本地令牌有效则自动恢复登录态，否则停留在登录界面
  if (getToken()) {
    try {
      user.value = (await api.me()).user
    } catch {
      setToken('')
    }
  }
  booting.value = false
})

async function pickProvider(p) {
  if (!p.available || switching.value || p.id === engine.value?.active) return
  switching.value = true
  recError.value = ''
  try {
    engine.value = await api.switchProvider(p.id)
  } catch (e) {
    recError.value = `切换模型失败：${e.message}`
  } finally {
    switching.value = false
  }
}

function onConnected(snap) {
  engine.value = snap
  recError.value = ''
}

function onAuthed(u) {
  user.value = u
  histTick.value++
}

async function logout() {
  try {
    await api.logout()
  } catch {
    // 本地登出不受影响
  }
  setToken('')
  user.value = null
}

function b64Of(dataUrl) {
  return dataUrl.includes(',') ? dataUrl.split(',')[1] : dataUrl
}

async function onConfirm(dataUrl) {
  photo.value = dataUrl
  rec.value = null
  gen.value = null
  poster.value = null
  audioUrl.value = ''
  ttsError.value = ''
  recError.value = ''
  loading.rec = true
  try {
    rec.value = await api.recognize(b64Of(dataUrl))
  } catch (e) {
    recError.value = e.message
  } finally {
    loading.rec = false
  }
}

async function generateAll() {
  const info = {
    name: rec.value.name,
    category: rec.value.category,
    origin: rec.value.origin,
    highlights: rec.value.highlights,
  }
  loading.copy = loading.poster = loading.audio = true
  ttsError.value = ''

  const copyTask = api.generate(info)
    .then((g) => (gen.value = g))
    .catch((e) => (recError.value = `文案生成失败：${e.message}`))
    .finally(() => (loading.copy = false))

  const posterTask = api.poster({ image: b64Of(photo.value), name: rec.value.name, tagline: '', origin: rec.value.origin })
    .then((p) => (poster.value = p))
    .catch((e) => (recError.value = `海报生成失败：${e.message}`))
    .finally(() => (loading.poster = false))

  // 语音文本依赖文案结果，先生成文案
  copyTask.then(async () => {
    if (!gen.value) return
    try {
      const t = await api.tts(`${gen.value.title}。${gen.value.story}`)
      audioUrl.value = t.url
    } catch (e) {
      ttsError.value = `语音生成失败：${e.message}（不影响其他三项）`
    } finally {
      loading.audio = false
    }
  })

  await Promise.allSettled([copyTask, posterTask])

  // 登录用户自动存档本次创作
  if (user.value && gen.value) {
    api
      .addHistory(rec.value.name, gen.value.title, poster.value?.url || '')
      .then(() => (histTick.value++))
      .catch(() => {})
  }
}
</script>

<template>
  <!-- 启动检查中 -->
  <div v-if="booting" class="flex min-h-screen items-center justify-center bg-stone-100">
    <div class="text-center">
      <div class="mx-auto flex h-14 w-14 animate-pulse items-center justify-center rounded-2xl bg-brand-600 text-2xl">🍊</div>
      <p class="mt-3 text-sm text-stone-400">正在进入山货有话说…</p>
    </div>
  </div>

  <!-- 未登录：登录 / 注册界面 -->
  <LoginScreen v-else-if="!user" @authed="onAuthed" />

  <!-- 主应用（仅登录后可见） -->
  <div v-else class="mx-auto min-h-screen max-w-2xl px-4 pb-16">
    <!-- 顶栏 -->
    <header class="flex items-center justify-between py-6">
      <div class="flex items-center gap-3">
        <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-600 text-xl shadow-md shadow-brand-600/30">🍊</div>
        <div>
          <h1 class="text-xl font-bold tracking-tight text-stone-900">山货有话说</h1>
          <p class="text-xs text-stone-500">AI 让每一份山货开口说话</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span
          class="rounded-full px-3 py-1.5 text-[11px] font-medium"
          :class="demoMode ? 'bg-harvest-400/20 text-harvest-600' : 'bg-brand-50 text-brand-700'"
        >
          {{ demoMode ? '演示模式' : 'AI 已连接' }}
        </span>
        <button
          v-if="user"
          class="flex items-center gap-1.5 rounded-full bg-stone-100 py-1 pl-2.5 pr-1.5 text-[11px] font-medium text-stone-700 transition hover:bg-stone-200"
          :title="'点击退出登录'"
          @click="logout"
        >
          👤 {{ user.nickname }}
          <span class="rounded-full bg-white px-1.5 py-0.5 text-[10px] text-stone-400">退出</span>
        </button>
      </div>
    </header>

    <!-- Hero -->
    <section class="rise mb-4 rounded-3xl bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500 p-6 text-white shadow-lg shadow-brand-700/25">
      <h2 class="text-2xl font-bold leading-snug">拍一张照片，<br />AI 为山货写文案、画海报、配语音</h2>
      <p class="mt-2 text-sm text-white/85">乡村振兴 · 科创赋能 ｜ 全国大学生数字媒体科技作品及创意竞赛参赛作品</p>
      <div class="mt-4 flex flex-wrap gap-2 text-[11px]">
        <span class="rounded-full bg-white/15 px-3 py-1">多模态识别</span>
        <span class="rounded-full bg-white/15 px-3 py-1">AIGC 海报</span>
        <span class="rounded-full bg-white/15 px-3 py-1">大模型文案</span>
        <span class="rounded-full bg-white/15 px-3 py-1">智能语音</span>
        <span class="rounded-full bg-white/15 px-3 py-1">数字讲解员</span>
      </div>
    </section>

    <!-- 模型引擎选择器 -->
    <section v-if="engine" class="rise mb-5 rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
      <div class="flex items-center justify-between gap-2">
        <span class="text-xs font-semibold text-stone-500">🧠 模型引擎</span>
        <div class="flex items-center gap-2">
          <span v-if="engine.active" class="text-[11px] text-brand-600">
            当前：{{ engine.providers.find((p) => p.id === engine.active)?.name }}
          </span>
          <span v-else class="text-[11px] text-harvest-600">未配置 Key · 演示模式</span>
          <button
            class="rounded-lg bg-brand-600 px-2.5 py-1 text-[11px] font-semibold text-white shadow-sm shadow-brand-600/25 transition hover:bg-brand-700 active:scale-[0.97]"
            @click="connectOpen = true"
          >
            ＋ 接入大模型
          </button>
        </div>
      </div>
      <div class="mt-2.5 flex flex-wrap gap-2">
        <button
          v-for="p in engine.providers"
          :key="p.id"
          class="rounded-xl border px-3 py-1.5 text-xs font-medium transition"
          :class="p.id === engine.active
            ? 'border-brand-600 bg-brand-600 text-white shadow-sm shadow-brand-600/25'
            : p.available
              ? 'border-stone-200 text-stone-600 hover:border-brand-400 hover:text-brand-700'
              : 'cursor-not-allowed border-stone-100 text-stone-300'"
          :title="p.available ? p.note : `${p.note}（需在 backend/.env 配置 ${p.note ? '对应 Key' : 'Key'}）`"
          @click="pickProvider(p)"
        >
          {{ p.name }}
          <span v-if="p.id === engine.active">✓</span>
          <span v-else-if="!p.available" class="ml-0.5 text-[10px]">未配置</span>
        </button>
      </div>
      <p class="mt-2 text-[11px] leading-relaxed text-stone-400">
        在 backend/.env 中配置对应厂商的 API Key 后即可启用并一键切换；识图/生图能力视厂商而定。
      </p>
    </section>

    <!-- 错误提示 -->
    <div v-if="recError" class="rise mb-4 rounded-2xl bg-red-50 p-4 text-sm text-red-600">⚠️ {{ recError }}</div>

    <!-- 步骤一：上传 -->
    <section class="mb-6">
      <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-stone-500">
        <span class="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-xs text-white">1</span>
        上传山货照片
      </h3>
      <UploadPanel @confirm="onConfirm" />
    </section>

    <!-- 步骤二：识别 + 四件套 -->
    <section v-if="photo" class="mb-6">
      <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-stone-500">
        <span class="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-xs text-white">2</span>
        AI 识别与创作
      </h3>
      <div v-if="loading.rec" class="flex items-center justify-center gap-2 rounded-3xl bg-white p-10 text-sm text-stone-500 shadow-sm">
        <span class="h-2 w-2 animate-ping rounded-full bg-brand-500"></span>
        正在识别照片中的山货…
      </div>
      <ResultsPanel
        v-else-if="rec"
        :rec="rec"
        :photo="photo"
        :gen="gen"
        :poster="poster"
        :audio-url="audioUrl"
        :tts-error="ttsError"
        :loading="loading"
        @generate="generateAll"
      />
    </section>

    <!-- 数字讲解员 -->
    <section class="mb-6">
      <h3 class="mb-3 flex items-center gap-2 text-sm font-semibold text-stone-500">
        <span class="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-xs text-white">3</span>
        云游乡村
      </h3>
      <GuidePanel />
    </section>

    <!-- 生成历史 -->
    <section class="mb-6">
      <HistoryPanel :user="user" :tick="histTick" />
    </section>

    <footer class="pt-4 text-center text-xs leading-relaxed text-stone-400">
      <p>《山货有话说》—— AI 助农数字文创平台 v0.4</p>
      <p class="mt-1">对应“乡村振兴·科创赋能”指定命题 ｜ 多模型切换 + 多模态大模型 + AIGC + TTS</p>
    </footer>

    <!-- 接入大模型弹窗 -->
    <ConnectModal
      :open="connectOpen"
      :providers="engine?.providers || []"
      :active-id="engine?.active || ''"
      @close="connectOpen = false"
      @connected="onConnected"
    />
  </div>
</template>
