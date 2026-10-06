<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({
  user: { type: Object, default: null },
  tick: { type: Number, default: 0 },
})
const emit = defineEmits(['need-login'])

const items = ref([])
const loading = ref(false)
const error = ref('')

const shown = computed(() => items.value.slice(0, 20))

function fmtTime(ts) {
  const d = new Date(ts * 1000)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}月${d.getDate()}日 ${p(d.getHours())}:${p(d.getMinutes())}`
}

async function load() {
  if (!props.user) {
    items.value = []
    return
  }
  loading.value = true
  error.value = ''
  try {
    items.value = (await api.history()).items
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function del(id) {
  try {
    await api.deleteHistory(id)
    items.value = items.value.filter((x) => x.id !== id)
  } catch (e) {
    error.value = e.message
  }
}

watch(() => [props.user, props.tick], load, { immediate: true })
</script>

<template>
  <div class="rise rounded-3xl border border-stone-200 bg-white p-5 shadow-sm">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-bold text-stone-900">🗂️ 我的生成历史</h3>
      <span v-if="user" class="text-xs text-stone-400">{{ items.length }} 条记录</span>
    </div>

    <!-- 未登录提示 -->
    <div v-if="!user" class="mt-4 rounded-2xl bg-stone-50 p-5 text-center">
      <p class="text-sm text-stone-500">登录后，每次生成的四件套会自动存档，随时回看</p>
      <button
        class="mt-3 rounded-xl bg-brand-600 px-5 py-2 text-sm font-semibold text-white shadow-md shadow-brand-600/30 transition hover:bg-brand-700"
        @click="emit('need-login')"
      >
        登录 / 注册
      </button>
    </div>

    <!-- 已登录 -->
    <template v-else>
      <div v-if="error" class="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-600">⚠️ {{ error }}</div>

      <div v-if="loading" class="mt-4 text-center text-xs text-stone-400">加载中…</div>

      <div v-else-if="items.length" class="mt-4 space-y-2.5">
        <div
          v-for="it in shown"
          :key="it.id"
          class="flex items-center gap-3 rounded-2xl border border-stone-100 p-3 transition hover:border-brand-200"
        >
          <img
            v-if="it.poster_url"
            :src="it.poster_url"
            alt="海报缩略图"
            class="h-14 w-11 shrink-0 rounded-lg object-cover shadow-sm"
          />
          <div v-else class="flex h-14 w-11 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-xl">🍊</div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-semibold text-stone-800">{{ it.name }}</p>
            <p class="truncate text-xs text-stone-500">{{ it.title || '山货四件套' }}</p>
            <p class="mt-0.5 text-[10px] text-stone-400">{{ fmtTime(it.created_at) }}</p>
          </div>
          <button
            class="shrink-0 rounded-lg p-2 text-xs text-stone-300 transition hover:bg-red-50 hover:text-red-500"
            title="删除该记录"
            @click="del(it.id)"
          >
            🗑
          </button>
        </div>
        <p v-if="items.length > shown.length" class="text-center text-[11px] text-stone-400">
          仅显示最近 {{ shown.length }} 条
        </p>
      </div>

      <div v-else class="mt-4 rounded-2xl bg-stone-50 p-5 text-center">
        <p class="text-sm text-stone-500">还没有生成记录，去上面传一张山货照片试试吧 📷</p>
      </div>
    </template>
  </div>
</template>
