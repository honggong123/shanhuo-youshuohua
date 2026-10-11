<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, getToken, setToken } from './api'
import UploadPanel from './components/UploadPanel.vue'
import ResultsPanel from './components/ResultsPanel.vue'
import GuidePanel from './components/GuidePanel.vue'
import ConnectModal from './components/ConnectModal.vue'
import LoginScreen from './components/LoginScreen.vue'
import HistoryPanel from './components/HistoryPanel.vue'
import AppIcon from './components/AppIcon.vue'
import BrandMark from './components/BrandMark.vue'

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

// 清空"创作"相关状态：切换账号时必须调用，否则上一个账号的识别结果/四件套会残留
function resetCreation() {
  photo.value = ''
  rec.value = null
  gen.value = null
  poster.value = null
  audioUrl.value = ''
  ttsError.value = ''
  recError.value = ''
  loading.rec = loading.copy = loading.poster = loading.audio = false
}

function onAuthed(u) {
  resetCreation()  // 登录成功后从干净状态开始，杜绝上一个账号的遗留
  user.value = u
  histTick.value++
  // 登录后重新拉取"我自己的"模型引擎状态（未登录时看到的是部署方默认）
  api
    .providers()
    .then((s) => (engine.value = s))
    .catch(() => {})
}

async function logout() {
  try {
    await api.logout()
  } catch {
    // 本地登出不受影响
  }
  setToken('')
  user.value = null
  resetCreation()
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
    rec.value = await api.recognize(dataUrl)
  } catch (e) {
    recError.value = e.message
  } finally {
    loading.rec = false
  }
}

async function generateAll() {
  const owner = user.value?.id  // 记录发起时的账号，防止中途切号后误存到别人名下
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

  const posterTask = api.poster({ image: photo.value, name: rec.value.name, tagline: '', origin: rec.value.origin })
    .then((p) => (poster.value = p))
    .catch((e) => (recError.value = `海报生成失败：${e.message}`))
    .finally(() => (loading.poster = false))

  // 语音文本依赖文案结果，先生成文案
  copyTask.then(async () => {
    try {
      // 注意：文案失败时也要复位 loading.audio，否则界面会永久卡在“创作中”且无法重试
      if (!gen.value) return
      const t = await api.tts(`${gen.value.title}。${gen.value.story}`)
      audioUrl.value = t.url
    } catch (e) {
      ttsError.value = `语音生成失败：${e.message}（不影响其他三项）`
    } finally {
      loading.audio = false
    }
  })

  await Promise.allSettled([copyTask, posterTask])

  // 登录用户自动存档本次创作（若生成过程中途切换了账号则不存，避免串号）
  if (user.value && gen.value && user.value.id === owner) {
    api
      .addHistory(rec.value.name, gen.value.title, poster.value?.url || '')
      .then(() => (histTick.value++))
      .catch(() => {})
  }
}
</script>

<template>
  <!-- 启动检查中 -->
  <div v-if="booting" class="flex min-h-screen items-center justify-center">
    <div class="text-center">
      <BrandMark :size="56" class="mx-auto animate-pulse" />
      <p class="mt-3 text-sm text-stone-400">正在进入山货有话说…</p>
    </div>
  </div>

  <!-- 未登录：登录 / 注册界面 -->
  <LoginScreen v-else-if="!user" @authed="onAuthed" />

  <!-- 主应用（仅登录后可见） -->
  <div v-else class="mx-auto min-h-screen max-w-2xl px-4 pb-16">
    <!-- 顶栏 -->
    <header class="rise flex items-center justify-between gap-2 py-6">
      <div class="flex min-w-0 items-center gap-3">
        <BrandMark :size="44" class="shrink-0" />
        <div class="min-w-0">
          <h1 class="whitespace-nowrap text-xl font-bold tracking-tight text-stone-900">山货有话说</h1>
          <p class="truncate text-xs text-stone-500">AI 让每一份山货开口说话</p>
        </div>
      </div>
      <div class="flex shrink-0 items-center gap-2">
        <span
          class="flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1.5 text-[11px] font-medium sm:px-3"
          :class="demoMode ? 'bg-harvest-400/20 text-harvest-600' : 'bg-brand-50 text-brand-700'"
        >
          <span
            class="h-1.5 w-1.5 shrink-0 rounded-full"
            :class="demoMode ? 'bg-harvest-500' : 'bg-brand-500'"
          ></span>
          <span class="hidden sm:inline">{{ demoMode ? '演示模式' : 'AI 已连接' }}</span>
          <span class="sm:hidden">{{ demoMode ? '演示' : '已连接' }}</span>
        </span>
        <button
          v-if="user"
          class="flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full bg-white/70 py-1 pl-2 pr-1.5 text-[11px] font-medium text-stone-700 ring-1 ring-stone-200 transition hover:bg-white"
          :title="'点击退出登录'"
          @click="logout"
        >
          <AppIcon name="user" :size="13" class="text-stone-400" />
          <span class="max-w-[56px] truncate">{{ user.nickname }}</span>
          <span class="hidden rounded-full bg-stone-100 px-1.5 py-0.5 text-[10px] text-stone-400 sm:inline">退出</span>
        </button>
      </div>
    </header>

    <!-- Hero -->
    <section class="rise d1 relative mb-4 overflow-hidden rounded-3xl bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500 p-6 text-white shadow-lg shadow-brand-700/25">
      <!-- 装饰层：不参与布局、不拦截点击 -->
      <div class="pointer-events-none absolute inset-0" aria-hidden="true">
        <!-- 顶部高光细线 -->
        <div class="absolute inset-x-0 top-0 h-px bg-white/30"></div>
        <!-- 光带扫过 -->
        <div class="sheen"></div>
        <!-- 左上冷色光晕 -->
        <div class="floaty-slow absolute -left-12 -top-14 h-40 w-40 rounded-full bg-white/10 blur-2xl"></div>
        <!-- 右下丰收色光晕 -->
        <div class="floaty absolute -bottom-16 -right-10 h-44 w-44 rounded-full bg-harvest-400/25 blur-2xl"></div>
        <!-- 梯田山峦插画（右下角水印式，压在标签行背后） -->
        <svg class="absolute -bottom-1 right-0 w-72 text-white sm:w-80" viewBox="0 0 320 140" fill="none">
          <circle cx="266" cy="28" r="16" fill="currentColor" opacity="0.16" />
          <path d="M0 140C58 96 108 120 158 100 208 80 258 108 320 82v58z" fill="currentColor" opacity="0.20" />
          <path d="M0 140C68 114 118 132 172 114 226 96 272 120 320 104v36z" fill="currentColor" opacity="0.32" />
        </svg>
      </div>

      <!-- 内容 -->
      <div class="relative">
        <h2 class="text-2xl font-bold leading-snug">拍一张照片，<br />AI 为山货写文案、画海报、配语音</h2>
        <p class="mt-2 text-sm text-white/85">乡村振兴 · 科创赋能 ｜ 全国大学生数字媒体科技作品及创意竞赛参赛作品</p>
        <div class="mt-4 flex flex-wrap gap-2 text-[11px]">
          <span class="rounded-full border border-white/20 bg-white/15 px-3 py-1 backdrop-blur-sm">多模态识别</span>
          <span class="rounded-full border border-white/20 bg-white/15 px-3 py-1 backdrop-blur-sm">AIGC 海报</span>
          <span class="rounded-full border border-white/20 bg-white/15 px-3 py-1 backdrop-blur-sm">大模型文案</span>
          <span class="rounded-full border border-white/20 bg-white/15 px-3 py-1 backdrop-blur-sm">智能语音</span>
          <span class="rounded-full border border-white/20 bg-white/15 px-3 py-1 backdrop-blur-sm">数字讲解员</span>
        </div>
      </div>
    </section>

    <!-- 模型引擎选择器 -->
    <section v-if="engine" class="rise d2 relative mb-5 overflow-hidden rounded-2xl border border-stone-200 bg-white p-4 pt-5 shadow-sm">
      <span class="card-accent" aria-hidden="true"></span>
      <div class="flex items-center justify-between gap-2">
        <span class="flex items-center gap-1.5 text-xs font-semibold text-stone-500">
          <AppIcon name="cpu" :size="15" class="text-brand-600" />
          模型引擎
        </span>
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
          :title="p.available ? p.note : `${p.note}（点“接入大模型”填入你自己的 Key 即可启用）`"
          @click="pickProvider(p)"
        >
          {{ p.name }}
          <span v-if="p.id === engine.active">✓</span>
          <span v-else-if="!p.available" class="ml-0.5 text-[10px]">未配置</span>
          <span v-if="p.mine" class="ml-1 text-[9px] opacity-80">·我的</span>
        </button>
      </div>
      <p class="mt-2 text-[11px] leading-relaxed text-stone-400">
        你接入的 Key <b>只绑定当前账号</b>，其他账号无法使用；未接入时自动使用平台默认模型。识图/生图能力随厂商而定，缺失时自动回退平台默认。
      </p>
    </section>

    <!-- 错误提示 -->
    <div v-if="recError" class="rise mb-4 rounded-2xl bg-red-50 p-4 text-sm text-red-600">⚠️ {{ recError }}</div>

    <!-- 步骤一：上传 -->
    <section class="mb-6">
      <h3 class="rise d2 mb-3 flex items-center gap-2.5 text-sm font-semibold text-stone-600">
        <span class="step-badge">1</span>
        <span>上传山货照片</span>
        <span class="h-px flex-1 bg-gradient-to-r from-brand-200 to-transparent" aria-hidden="true"></span>
      </h3>
      <UploadPanel @confirm="onConfirm" />
    </section>

    <!-- 步骤二：识别 + 四件套 -->
    <section v-if="photo" class="mb-6">
      <h3 class="rise mb-3 flex items-center gap-2.5 text-sm font-semibold text-stone-600">
        <span class="step-badge">2</span>
        <span>AI 识别与创作</span>
        <span class="h-px flex-1 bg-gradient-to-r from-brand-200 to-transparent" aria-hidden="true"></span>
      </h3>
      <div v-if="loading.rec" class="flex items-center justify-center gap-3 rounded-3xl border border-stone-200 bg-white p-10 text-sm text-stone-500 shadow-sm">
        <span class="relative flex h-3 w-3">
          <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-75"></span>
          <span class="relative inline-flex h-3 w-3 rounded-full bg-brand-600"></span>
        </span>
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
      <h3 class="rise mb-3 flex items-center gap-2.5 text-sm font-semibold text-stone-600">
        <span class="step-badge">3</span>
        <span>云游乡村</span>
        <span class="h-px flex-1 bg-gradient-to-r from-brand-200 to-transparent" aria-hidden="true"></span>
      </h3>
      <GuidePanel />
    </section>

    <!-- 生成历史 -->
    <section class="mb-6">
      <HistoryPanel :user="user" :tick="histTick" />
    </section>

    <footer class="pt-6 text-center text-xs leading-relaxed text-stone-400">
      <div class="mb-4 flex items-center justify-center gap-3" aria-hidden="true">
        <span class="h-px w-16 bg-gradient-to-r from-transparent to-brand-200"></span>
        <AppIcon name="leaf" :size="16" class="text-brand-400" />
        <span class="h-px w-16 bg-gradient-to-l from-transparent to-brand-200"></span>
      </div>
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
