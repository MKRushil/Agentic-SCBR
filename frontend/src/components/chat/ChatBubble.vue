<script setup lang="ts">
import { computed } from 'vue'
import { formatDate } from '@/utils/formatters'

const props = defineProps<{
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}>()

const isUser = computed(() => props.role === 'user')
const isSystem = computed(() => props.role === 'system')

const bubbleClass = computed(() => {
  if (isSystem.value) return 'bg-gray-100 text-gray-500 text-xs py-1 px-3 rounded-full mx-auto'
  if (isUser.value) return 'bg-emerald-100 text-slate-800 rounded-br-none'
  return 'bg-white border border-slate-200 text-slate-800 rounded-bl-none shadow-sm'
})
</script>

<template>
  <div :class="['flex mb-4', isUser ? 'justify-end' : isSystem ? 'justify-center' : 'justify-start']">
    <div 
      class="max-w-[80%] p-3 rounded-2xl relative"
      :class="bubbleClass"
    >
      <p class="whitespace-pre-wrap text-sm leading-relaxed">{{ content }}</p>
      <span v-if="!isSystem" class="text-[10px] text-slate-400 absolute bottom-1 right-2 opacity-70">
        {{ formatDate(timestamp).split(' ')[1] }}
      </span>
    </div>
  </div>
</template>