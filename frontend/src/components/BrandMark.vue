<script setup>
/* 品牌标记：绿色圆角块 + 白色对话气泡 + 气泡内山峦与太阳
   语义：气泡 = "有话说"，山峦 = "山货"，太阳 = "丰收"
   替代原先的 🍊 emoji，避免不同系统 emoji 字体差异导致观感不一致 */
defineProps({
  size: { type: [Number, String], default: 44 },
  radius: { type: [Number, String], default: 14 },
})
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 48 48" fill="none" aria-hidden="true" focusable="false">
    <defs>
      <linearGradient id="brand-mark-grad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#4d9950" />
        <stop offset="1" stop-color="#2b5630" />
      </linearGradient>
    </defs>
    <rect width="48" height="48" :rx="radius" fill="url(#brand-mark-grad)" />
    <!-- 对话气泡 -->
    <path
      d="M14 12h20a4 4 0 0 1 4 4v12a4 4 0 0 1-4 4H26l-7 6v-6h-5a4 4 0 0 1-4-4V16a4 4 0 0 1 4-4z"
      fill="#ffffff"
      fill-opacity="0.96"
    />
    <!-- 山峦 -->
    <path d="M13 30l7-10 4.5 6 3.5-4.5L35 30z" fill="#3d8042" />
    <!-- 太阳 -->
    <circle cx="29.5" cy="19.5" r="2.6" fill="#ee9d2b" />
  </svg>
</template>
