<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import { Send } from 'lucide-vue-next'

// 規格書 5.1: LLM10 防禦 - 前端強制限制
const MAX_LENGTH = 1000 
const inputText = ref('')
const chatStore = useChatStore()

const charCount = computed(() => inputText.value.length)
const isOverLimit = computed(() => charCount.value > MAX_LENGTH)

const handleSend = () => {
  if (!inputText.value.trim() || chatStore.isProcessing || isOverLimit.value) return
  
  chatStore.sendMessage(inputText.value)
  inputText.value = ''
}
</script>

<template>
  <div class="p-4 bg-white border-t border-slate-200">
    <!-- 字數統計與警告 -->
    <div class="flex justify-between items-center mb-2">
      <span 
        class="text-xs"
        :class="isOverLimit ? 'text-red-500 font-bold' : 'text-slate-400'"
      >
        {{ charCount }} / {{ MAX_LENGTH }} 字
      </span>
      <span v-if="isOverLimit" class="text-xs text-red-500">
        輸入過長，請精簡描述。
      </span>
    </div>

    <div class="relative">
      <textarea 
        v-model="inputText"
        rows="3"
        class="w-full p-3 pr-12 text-sm border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500 transition"
        :class="isOverLimit ? 'border-red-300 bg-red-50' : 'border-slate-300'"
        placeholder="請描述病患主訴、症狀 (如: 發熱、惡寒、脈象...)"
        @keydown.enter.prevent="handleSend"
      ></textarea>
      
      <button 
        @click="handleSend"
        :disabled="chatStore.isProcessing || !inputText.trim() || isOverLimit"
        class="absolute bottom-3 right-3 p-2 rounded-full bg-emerald-600 text-white disabled:bg-slate-300 disabled:cursor-not-allowed hover:bg-emerald-700 transition shadow-sm"
      >
        <Send class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>