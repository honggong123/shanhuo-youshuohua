<script setup>
import { ref } from 'vue'
import AppIcon from './AppIcon.vue'

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
  <div class="rise d3">
    <input ref="inputRef" type="file" accept="image/*" class="hidden" @change="onFile" />

    <!-- 空状态：上传区 -->
    <div
      v-if="!preview"
      class="group relative cursor-pointer overflow-hidden rounded-3xl border-2 border-dashed border-brand-300 bg-white/80 px-6 py-12 text-center shadow-sm transition duration-300 hover:border-brand-500 hover:bg-brand-50/70 hover:shadow-md"
      :class="{ 'border-brand-600 bg-brand-50': dragging }"
      @click="pick"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
    >
      <!-- 装饰层：内层柔光 + 四角取景框 + 扫描线 -->
      <span class="upload-glow" aria-hidden="true"></span>
      <span class="vf vf-tl" aria-hidden="true"></span>
      <span class="vf vf-tr" aria-hidden="true"></span>
      <span class="vf vf-bl" aria-hidden="true"></span>
      <span class="vf vf-br" aria-hidden="true"></span>
      <span class="scanline" aria-hidden="true"></span>

      <!-- 内容 -->
      <div class="relative">
        <!-- 相机图标 + 呼吸光环 + 漂浮小圆点 -->
        <div class="relative mx-auto mb-4 h-20 w-20">
          <span class="halo absolute inset-0 rounded-3xl bg-brand-400/40" aria-hidden="true"></span>
          <span class="absolute -inset-2 rounded-[26px] bg-brand-400/20 blur-xl" aria-hidden="true"></span>
          <span class="relative flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-brand-50 to-brand-100 text-brand-600 shadow-sm ring-1 ring-brand-200">
            <AppIcon name="camera" :size="38" :stroke="1.7" />
          </span>
          <span class="floaty absolute -right-2 top-1 h-2.5 w-2.5 rounded-full bg-harvest-400" aria-hidden="true"></span>
          <span class="floaty-slow absolute -left-3 bottom-2 h-2 w-2 rounded-full bg-brand-300" aria-hidden="true"></span>
        </div>

        <p class="text-lg font-semibold text-brand-800">拍摄或上传一张农产品照片</p>
        <p class="mt-1 text-sm text-stone-500">点击选择 / 手机直接拍照 / 拖拽图片到这里</p>

        <!-- 功能性小标签 -->
        <div class="mt-3 flex flex-wrap items-center justify-center gap-1.5">
          <span class="chip"><AppIcon name="image" :size="12" /> JPG / PNG</span>
          <span class="chip"><AppIcon name="shield" :size="12" /> ≤ 10MB</span>
          <span class="chip"><AppIcon name="spark" :size="12" /> 本地预览</span>
        </div>

        <span class="mt-5 inline-flex items-center gap-1.5 rounded-full bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white shadow-md shadow-brand-600/30 transition group-hover:bg-brand-700">
          <AppIcon name="upload" :size="16" />
          选择照片
        </span>
      </div>
    </div>

    <!-- 预览态 -->
    <div v-else class="relative overflow-hidden rounded-3xl border border-stone-200 bg-white shadow-sm">
      <span class="card-accent" aria-hidden="true"></span>
      <img :src="preview" alt="待识别照片" class="max-h-[420px] w-full bg-stone-50 object-contain" />
      <div class="flex gap-3 p-4">
        <button
          class="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-stone-200 px-4 py-3 text-sm font-medium text-stone-600 transition hover:border-brand-300 hover:bg-brand-50"
          @click="pick"
        >
          <AppIcon name="refresh" :size="16" />
          重新选择
        </button>
        <button
          class="flex flex-[2] items-center justify-center gap-1.5 rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white shadow-md shadow-brand-600/30 transition hover:bg-brand-700 active:scale-[0.98]"
          @click="confirm"
        >
          <AppIcon name="sparkles" :size="16" />
          开始 AI 识别
        </button>
      </div>
    </div>
  </div>
</template>
