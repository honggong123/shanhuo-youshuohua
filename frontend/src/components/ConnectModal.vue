<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({
  open: { type: Boolean, default: false },
  providers: { type: Array, default: () => [] },
  activeId: { type: String, default: '' },
})
const emit = defineEmits(['close', 'connected'])

const selectedId = ref('')
const apiKey = ref('')
const showKey = ref(false)
const connecting = ref(false)
const error = ref('')

const DEFAULT_ID = 'glm'

watch(
  () => props.open,
  (open) => {
    if (open) {
      error.value = ''
      apiKey.value = ''
      showKey.value = false
      connecting.value = false
      // 默认选中：当前未接入的推荐厂商（glm 优先），已接入的可覆盖 Key
      selectedId.value = props.providers.some((p) => p.id === DEFAULT_ID && !p.available)
        ? DEFAULT_ID
        : props.providers.find((p) => !p.available)?.id || props.providers[0]?.id || DEFAULT_ID
    }
  },
)

const selected = computed(() => props.providers.find((p) => p.id === selectedId.value))

async function connect() {
  if (!apiKey.value.trim()) {
    error.value = '请先粘贴 API Key'
    return
  }
  connecting.value = true
  error.value = ''
  try {
    const snap = await api.connectProvider(selectedId.value, apiKey.value.trim())
    emit('connected', snap)
    emit('close')
  } catch (e) {
    error.value = e.message
  } finally {
    connecting.value = false
  }
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 flex items-end justify-center bg-stone-900/50 p-0 backdrop-blur-sm sm:items-center sm:p-6"
    @click.self="emit('close')"
  >
    <div class="rise w-full max-w-md rounded-t-3xl bg-white p-6 shadow-2xl sm:rounded-3xl">
      <!-- 标题 -->
      <div class="flex items-start justify-between">
        <div>
          <h3 class="text-lg font-bold text-stone-900">🔌 接入大模型</h3>
          <p class="mt-1 text-xs text-stone-500">粘贴 API Key，验证通过后立即生效并保存到本机</p>
        </div>
        <button class="rounded-lg p-1.5 text-stone-400 transition hover:bg-stone-100 hover:text-stone-600" @click="emit('close')">
          ✕
        </button>
      </div>

      <!-- 厂商选择 -->
      <p class="mt-5 text-xs font-semibold text-stone-500">选择厂商</p>
      <div class="mt-2 grid grid-cols-2 gap-2">
        <button
          v-for="p in providers"
          :key="p.id"
          class="rounded-xl border px-3 py-2.5 text-left text-sm transition"
          :class="selectedId === p.id
            ? 'border-brand-600 bg-brand-50 ring-1 ring-brand-600'
            : 'border-stone-200 hover:border-stone-300'"
          @click="selectedId = p.id"
        >
          <span class="font-semibold text-stone-800">{{ p.name }}</span>
          <span v-if="p.id === activeId" class="ml-1 rounded bg-brand-600 px-1 py-0.5 text-[10px] text-white">使用中</span>
          <p class="mt-0.5 text-[10px] leading-tight text-stone-400">{{ p.available ? '已接入' : p.vision_model || p.img_model ? '支持识图' : '仅文本' }}</p>
        </button>
      </div>

      <!-- Key 输入 -->
      <div class="mt-4 flex items-center justify-between">
        <p class="text-xs font-semibold text-stone-500">API Key</p>
        <a
          v-if="selected?.signup_url"
          :href="selected.signup_url"
          target="_blank"
          rel="noopener"
          class="text-xs font-medium text-brand-600 underline-offset-2 hover:underline"
        >
          {{ selected.name }} 官网获取 ↗
        </a>
      </div>
      <div class="mt-2 flex items-center gap-2 rounded-xl border border-stone-200 px-3 py-2.5 transition focus-within:border-brand-500">
        <input
          v-model="apiKey"
          :type="showKey ? 'text' : 'password'"
          placeholder="粘贴你的 API Key"
          class="w-full bg-transparent text-sm outline-none"
          @keyup.enter="connect"
        />
        <button class="shrink-0 text-xs text-stone-400 hover:text-stone-600" @click="showKey = !showKey">
          {{ showKey ? '隐藏' : '显示' }}
        </button>
      </div>

      <p v-if="selected" class="mt-2 text-[11px] leading-relaxed text-stone-400">
        💡 {{ selected.note }}。Key 仅保存在本机 backend/.env，不会上传到任何服务器。
      </p>

      <!-- 错误提示 -->
      <div v-if="error" class="mt-3 rounded-xl bg-red-50 p-3 text-xs leading-relaxed text-red-600">⚠️ {{ error }}</div>

      <!-- 操作按钮 -->
      <div class="mt-5 flex gap-3">
        <button
          class="flex-1 rounded-xl border border-stone-200 px-4 py-3 text-sm font-medium text-stone-600 transition hover:bg-stone-50"
          @click="emit('close')"
        >
          取消
        </button>
        <button
          class="flex-[2] rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-brand-600/30 transition hover:bg-brand-700 active:scale-[0.98] disabled:opacity-60"
          :disabled="connecting"
          @click="connect"
        >
          {{ connecting ? '正在验证连接…' : '验证并连接' }}
        </button>
      </div>
    </div>
  </div>
</template>
