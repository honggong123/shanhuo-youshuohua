<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  rec: { type: Object, required: true },
  photo: { type: String, required: true },
  gen: { type: Object, default: null },
  poster: { type: Object, default: null },
  audioUrl: { type: String, default: '' },
  ttsError: { type: String, default: '' },
  loading: { type: Object, required: true },
})
const emit = defineEmits(['generate'])

const tab = ref('copy')
const tabs = [
  { key: 'copy', label: '✍️ 卖点文案' },
  { key: 'poster', label: '🖼️ 文创海报' },
  { key: 'audio', label: '🔊 语音介绍' },
  { key: 'script', label: '🎬 视频脚本' },
]

const audioText = computed(() => {
  if (!props.gen) return ''
  return `${props.gen.title}。${props.gen.story}`
})

const anyLoading = computed(() =>
  props.loading.copy || props.loading.poster || props.loading.audio,
)
</script>

<template>
  <div class="rise space-y-5">
    <!-- 识别结果卡 -->
    <div class="rounded-3xl border border-stone-200 bg-white p-5 shadow-sm">
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold tracking-wider text-brand-600">AI 识别结果</span>
        <span v-if="rec.demo" class="rounded-full bg-harvest-400/20 px-2.5 py-1 text-xs font-medium text-harvest-600">
          演示数据 · 配置 Key 后为真实识别
        </span>
      </div>
      <h3 class="mt-2 text-2xl font-bold text-stone-900">{{ rec.name }}</h3>
      <div class="mt-2 flex flex-wrap gap-2">
        <span class="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">{{ rec.category }}</span>
        <span class="rounded-full bg-stone-100 px-3 py-1 text-xs font-medium text-stone-600">📍 {{ rec.origin }}</span>
      </div>
      <p class="mt-3 text-sm leading-relaxed text-stone-600">{{ rec.description }}</p>
      <div class="mt-3 flex flex-wrap gap-2">
        <span v-for="h in rec.highlights" :key="h" class="rounded-lg bg-harvest-400/15 px-2.5 py-1 text-xs text-harvest-600">
          ✦ {{ h }}
        </span>
      </div>
    </div>

    <!-- 生成按钮 -->
    <button
      v-if="!gen && !anyLoading"
      class="w-full rounded-2xl bg-gradient-to-r from-brand-600 to-harvest-500 px-4 py-4 text-base font-bold text-white shadow-lg shadow-brand-600/30 transition hover:brightness-105 active:scale-[0.99]"
      @click="emit('generate')"
    >
      ✨ 一键生成四件套（海报 · 文案 · 语音 · 脚本）
    </button>
    <div v-else-if="anyLoading" class="flex items-center justify-center gap-2 rounded-2xl bg-white px-4 py-4 text-sm text-stone-500 shadow-sm">
      <span class="h-2 w-2 animate-ping rounded-full bg-brand-500"></span>
      AI 正在创作中，请稍候…
    </div>

    <!-- 四件套 Tabs -->
    <div v-if="gen || anyLoading" class="overflow-hidden rounded-3xl border border-stone-200 bg-white shadow-sm">
      <div class="flex border-b border-stone-100 bg-stone-50/60">
        <button
          v-for="t in tabs"
          :key="t.key"
          class="flex-1 px-2 py-3 text-xs font-semibold transition sm:text-sm"
          :class="tab === t.key ? 'border-b-2 border-brand-600 text-brand-700' : 'text-stone-400 hover:text-stone-600'"
          @click="tab = t.key"
        >
          {{ t.label }}
        </button>
      </div>

      <div class="p-5">
        <!-- 文案 -->
        <div v-if="tab === 'copy'">
          <div v-if="gen" class="space-y-4">
            <div class="flex items-center gap-2">
              <h4 class="text-xl font-bold text-stone-900">{{ gen.title }}</h4>
              <span v-if="gen.demo" class="rounded-full bg-harvest-400/20 px-2 py-0.5 text-[11px] text-harvest-600">演示数据</span>
            </div>
            <ul class="space-y-2">
              <li v-for="p in gen.selling_points" :key="p" class="flex gap-2 text-sm text-stone-700">
                <span class="text-harvest-500">✔</span>{{ p }}
              </li>
            </ul>
            <p class="rounded-2xl bg-brand-50 p-4 text-sm leading-relaxed text-stone-700">{{ gen.story }}</p>
            <div class="flex flex-wrap gap-2">
              <span v-for="h in gen.hashtags" :key="h" class="text-xs font-medium text-brand-600">{{ h }}</span>
            </div>
          </div>
          <div v-else class="animate-pulse space-y-3 py-2">
            <div class="h-6 w-2/3 rounded bg-stone-100"></div>
            <div class="h-4 w-full rounded bg-stone-100"></div>
            <div class="h-4 w-5/6 rounded bg-stone-100"></div>
          </div>
        </div>

        <!-- 海报 -->
        <div v-if="tab === 'poster'">
          <div v-if="poster" class="space-y-3">
            <img :src="poster.url" alt="文创海报" class="mx-auto max-h-[480px] rounded-2xl shadow-md" />
            <div class="flex items-center justify-between">
              <span class="text-xs text-stone-400">{{ poster.ai_art ? 'AI 底图 + 文字排版' : '本地模板合成（配置生图 Key 后为 AI 底图）' }}</span>
              <a :href="poster.url" download="山货海报.jpg" class="rounded-lg bg-brand-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-brand-700">
                ⬇ 下载海报
              </a>
            </div>
          </div>
          <div v-else class="flex h-64 items-center justify-center rounded-2xl bg-stone-50 text-sm text-stone-400">海报绘制中…</div>
        </div>

        <!-- 语音 -->
        <div v-if="tab === 'audio'">
          <div v-if="audioUrl" class="space-y-3">
            <audio :src="audioUrl" controls class="w-full"></audio>
            <p class="rounded-2xl bg-stone-50 p-4 text-sm leading-relaxed text-stone-600">{{ audioText }}</p>
          </div>
          <div v-else-if="ttsError" class="rounded-2xl bg-red-50 p-4 text-sm text-red-600">⚠️ {{ ttsError }}</div>
          <div v-else class="flex h-32 items-center justify-center rounded-2xl bg-stone-50 text-sm text-stone-400">语音合成中…</div>
        </div>

        <!-- 脚本 -->
        <div v-if="tab === 'script'">
          <div v-if="gen" class="space-y-3">
            <div v-for="s in gen.video_script" :key="s.shot" class="rounded-2xl border border-stone-100 p-4">
              <div class="flex items-center gap-2">
                <span class="rounded-md bg-brand-600 px-2 py-0.5 text-[11px] font-bold text-white">{{ s.shot }}</span>
                <span class="text-xs text-stone-500">🎬 {{ s.visual }}</span>
              </div>
              <p class="mt-2 text-sm leading-relaxed text-stone-700">“{{ s.narration }}”</p>
            </div>
          </div>
          <div v-else class="flex h-48 items-center justify-center rounded-2xl bg-stone-50 text-sm text-stone-400">脚本生成中…</div>
        </div>
      </div>
    </div>
  </div>
</template>
