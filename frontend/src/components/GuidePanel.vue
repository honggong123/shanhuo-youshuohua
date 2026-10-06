<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const villages = ref([])
const current = ref('')
const selectedProvince = ref('全部')
const story = ref('')
const audioUrl = ref('')
const question = ref('')
const loadingStory = ref(false)
const loadingAudio = ref(false)
const error = ref('')
const demo = ref(false)

onMounted(async () => {
  try {
    villages.value = await api.villages()
    current.value = villages.value[0]?.id || ''
  } catch {
    error.value = '村落数据加载失败'
  }
})

const provinces = computed(() => [...new Set(villages.value.map((v) => v.province))])
const filteredVillages = computed(() =>
  selectedProvince.value === '全部'
    ? villages.value
    : villages.value.filter((v) => v.province === selectedProvince.value),
)

function pickProvince(p) {
  selectedProvince.value = p
  // 若当前选中村落不在新省份里，自动切到该省第一个村落
  if (!filteredVillages.value.some((v) => v.id === current.value)) {
    current.value = filteredVillages.value[0]?.id || ''
  }
}

async function tell() {
  if (!current.value) return
  loadingStory.value = true
  error.value = ''
  audioUrl.value = ''
  try {
    const res = await api.guide(current.value)
    story.value = res.story
    demo.value = res.demo
    loadingAudio.value = true
    const t = await api.tts(res.story)
    audioUrl.value = t.url
  } catch (e) {
    error.value = e.message
  } finally {
    loadingStory.value = false
    loadingAudio.value = false
  }
}

async function ask() {
  if (!question.value.trim()) return
  loadingStory.value = true
  error.value = ''
  audioUrl.value = ''
  try {
    const res = await api.guide(current.value, question.value.trim())
    story.value = res.story
    demo.value = res.demo
  } catch (e) {
    error.value = e.message
  } finally {
    loadingStory.value = false
  }
}
</script>

<template>
  <div class="rise rounded-3xl border border-stone-200 bg-white p-5 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-bold text-stone-900">🧭 AI 数字讲解员</h3>
      <span class="text-xs text-stone-400">云游乡村 · 语音讲解</span>
    </div>

    <!-- 省份筛选 -->
    <div class="mt-4 flex flex-wrap gap-1.5">
      <button
        v-for="p in ['全部', ...provinces]"
        :key="p"
        class="rounded-lg border px-2.5 py-1 text-xs font-medium transition"
        :class="selectedProvince === p
          ? 'border-stone-800 bg-stone-800 text-white'
          : 'border-stone-200 text-stone-500 hover:border-stone-400 hover:text-stone-700'"
        @click="pickProvince(p)"
      >
        {{ p }}
      </button>
    </div>

    <!-- 村落选择（随省份筛选） -->
    <div class="mt-3 flex flex-wrap gap-2">
      <button
        v-for="v in filteredVillages"
        :key="v.id"
        class="rounded-xl border px-3.5 py-2 text-sm font-medium transition"
        :class="current === v.id
          ? 'border-brand-600 bg-brand-600 text-white shadow-md shadow-brand-600/25'
          : 'border-stone-200 bg-white text-stone-600 hover:border-brand-400 hover:text-brand-700'"
        @click="current = v.id"
      >
        {{ v.name }}
      </button>
      <p v-if="!filteredVillages.length" class="text-xs text-stone-400">该省份暂无村落</p>
    </div>
    <p class="mt-2 text-[11px] text-stone-400">
      已收录 {{ villages.length }} 个村落 · 覆盖 {{ provinces.length }} 个省区
    </p>

    <button
      class="mt-4 w-full rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-brand-600/30 transition hover:bg-brand-700 active:scale-[0.99]"
      :disabled="loadingStory"
      @click="tell"
    >
      {{ loadingStory ? '讲解员准备中…' : '🎙️ 生成沉浸式讲解' }}
    </button>

    <div v-if="error" class="mt-3 rounded-xl bg-red-50 p-3 text-sm text-red-600">⚠️ {{ error }}</div>

    <div v-if="story" class="mt-4 space-y-3">
      <p class="rounded-2xl bg-brand-50 p-4 text-sm leading-loose text-stone-700">{{ story }}</p>
      <span v-if="demo" class="text-[11px] text-harvest-600">演示文案 · 配置 Key 后由大模型实时生成</span>
      <audio v-if="audioUrl" :src="audioUrl" controls class="w-full"></audio>
      <div v-else-if="loadingAudio" class="text-center text-xs text-stone-400">语音合成中…</div>
    </div>

    <div class="mt-4 flex gap-2">
      <input
        v-model="question"
        type="text"
        placeholder="向讲解员提问，如：这里有什么好吃的？"
        class="flex-1 rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none transition focus:border-brand-500"
        @keyup.enter="ask"
      />
      <button
        class="rounded-xl bg-stone-800 px-4 py-3 text-sm font-semibold text-white transition hover:bg-stone-700 active:scale-[0.98]"
        :disabled="loadingStory"
        @click="ask"
      >
        提问
      </button>
    </div>
  </div>
</template>
