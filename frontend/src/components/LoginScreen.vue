<script setup>
import { ref } from 'vue'
import { api, setToken } from '../api'
import BrandMark from './BrandMark.vue'

const emit = defineEmits(['authed'])

const tab = ref('login')
const username = ref('')
const password = ref('')
const nickname = ref('')
const busy = ref(false)
const error = ref('')

async function submit() {
  if (!username.value.trim() || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  busy.value = true
  error.value = ''
  try {
    let res
    if (tab.value === 'register') {
      res = await api.register(username.value.trim(), password.value, nickname.value)
    } else {
      res = await api.login(username.value.trim(), password.value)
    }
    setToken(res.token)
    emit('authed', res.user)
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-br from-brand-700 via-brand-600 to-brand-500 px-4 py-10">
    <!-- 背景装饰层 -->
    <div class="pointer-events-none absolute inset-0" aria-hidden="true">
      <div class="sheen"></div>
      <div class="absolute inset-x-0 top-0 h-px bg-white/30"></div>
      <!-- 光晕 -->
      <div class="floaty-slow absolute -left-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-2xl"></div>
      <div class="floaty absolute -bottom-20 -right-10 h-72 w-72 rounded-full bg-harvest-400/25 blur-2xl"></div>
      <!-- 梯田山峦插画（底部水印） -->
      <svg class="absolute bottom-0 left-0 w-full text-white" viewBox="0 0 375 150" fill="none">
        <circle cx="300" cy="34" r="20" fill="currentColor" opacity="0.14" />
        <path d="M0 150C62 104 116 128 172 106 228 84 282 114 375 86v64z" fill="currentColor" opacity="0.10" />
        <path d="M0 150C74 122 128 140 186 120 244 100 296 126 375 108v42z" fill="currentColor" opacity="0.14" />
      </svg>
      <!-- 漂浮叶片点缀 -->
      <svg class="floaty absolute left-6 top-24 w-8 text-white/25" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M5.5 18.5C5.5 10 11.5 4.8 20 4.5c.3 8.5-5 14.5-13.5 14.5z" />
        <path d="M5.5 18.5L3.2 20.8" />
      </svg>
      <svg class="floaty-slow absolute right-8 top-32 w-10 text-white/20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 19h18L14.5 8l-3.2 5-2.1-3z" />
      </svg>
    </div>

    <div class="rise relative w-full max-w-sm">
      <!-- 品牌区 -->
      <div class="mb-6 text-center text-white">
        <BrandMark :size="64" class="mx-auto drop-shadow-lg" />
        <h1 class="mt-3 text-2xl font-bold tracking-tight">山货有话说</h1>
        <p class="mt-1 text-sm text-white/85">AI 让每一份山货开口说话</p>
      </div>

      <!-- 表单卡片 -->
      <div class="relative overflow-hidden rounded-3xl bg-white p-6 shadow-2xl">
        <span class="card-accent" aria-hidden="true"></span>
        <div class="flex rounded-xl bg-stone-100 p-1">
          <button
            class="flex-1 rounded-lg py-2 text-sm font-semibold transition"
            :class="tab === 'login' ? 'bg-white text-stone-900 shadow-sm' : 'text-stone-500'"
            @click="tab = 'login'; error = ''"
          >
            登 录
          </button>
          <button
            class="flex-1 rounded-lg py-2 text-sm font-semibold transition"
            :class="tab === 'register' ? 'bg-white text-stone-900 shadow-sm' : 'text-stone-500'"
            @click="tab = 'register'; error = ''"
          >
            注 册
          </button>
        </div>

        <div class="mt-4 space-y-3">
          <input
            v-model="username"
            type="text"
            placeholder="用户名（2~20 个字符）"
            class="w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none transition focus:border-brand-500"
            @keyup.enter="submit"
          />
          <input
            v-if="tab === 'register'"
            v-model="nickname"
            type="text"
            placeholder="昵称（选填，默认同用户名）"
            class="w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none transition focus:border-brand-500"
            @keyup.enter="submit"
          />
          <input
            v-model="password"
            type="password"
            :placeholder="tab === 'register' ? '密码（至少 6 位）' : '密码'"
            class="w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none transition focus:border-brand-500"
            @keyup.enter="submit"
          />
        </div>

        <div v-if="error" class="mt-3 rounded-xl bg-red-50 p-3 text-xs leading-relaxed text-red-600">⚠️ {{ error }}</div>

        <button
          class="mt-5 w-full rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-brand-600/30 transition hover:bg-brand-700 active:scale-[0.98] disabled:opacity-60"
          :disabled="busy"
          @click="submit"
        >
          {{ busy ? '请稍候…' : tab === 'login' ? '进入平台' : '注册并进入' }}
        </button>

        <p class="mt-4 text-center text-[11px] leading-relaxed text-stone-400">
          登录后可生成山货四件套、云游乡村，创作自动存档<br />
          密码加密存储，令牌保存在本机浏览器中
        </p>
      </div>

      <p class="mt-5 text-center text-[11px] leading-relaxed text-white/70">
        乡村振兴 · 科创赋能<br />全国大学生数字媒体科技作品及创意竞赛参赛作品
      </p>
    </div>
  </div>
</template>
