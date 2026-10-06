<script setup>
import { ref } from 'vue'

const emit = defineEmits(['confirm'])
const inputRef = ref(null)
const dragging = ref(false)
const preview = ref(null)

function pick() {
  inputRef.value?.click()
}

function onFile(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (file) read(file)
}

function onDrop(e) {
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) read(file)
}

function read(file) {
  if (file.size > 10 * 1024 * 1024) {
    alert('图片请小于 10MB')
    return
  }
  const reader = new FileReader()
  reader.onload = () => (preview.value = reader.result)
  reader.readAsDataURL(file)
}

function confirm() {
  if (preview.value) emit('confirm', preview.value)
}
</script>

<template>
  <div class="rise">
    <input ref="inputRef" type="file" accept="image/*" class="hidden" @change="onFile" />

    <div
      v-if="!preview"
      class="flex cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-brand-300 bg-white/70 px-6 py-14 text-center transition hover:border-brand-500 hover:bg-brand-50"
      :class="{ 'border-brand-600 bg-brand-50': dragging }"
      @click="pick"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
    >
      <div class="text-5xl">📷</div>
      <p class="mt-4 text-lg font-semibold text-brand-800">拍摄或上传一张农产品照片</p>
      <p class="mt-1 text-sm text-stone-500">点击选择 / 手机直接拍照 / 拖拽图片到这里（≤10MB）</p>
      <span class="mt-5 rounded-full bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white shadow-md shadow-brand-600/30">
        选择照片
      </span>
    </div>

    <div v-else class="overflow-hidden rounded-3xl border border-stone-200 bg-white shadow-sm">
      <img :src="preview" alt="待识别照片" class="max-h-[420px] w-full object-contain bg-stone-50" />
      <div class="flex gap-3 p-4">
        <button
          class="flex-1 rounded-xl border border-stone-200 px-4 py-3 text-sm font-medium text-stone-600 transition hover:bg-stone-50"
          @click="pick"
        >
          🔄 重新选择
        </button>
        <button
          class="flex-[2] rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-brand-600/30 transition hover:bg-brand-700 active:scale-[0.98]"
          @click="confirm"
        >
          🤖 开始 AI 识别
        </button>
      </div>
    </div>
  </div>
</template>
