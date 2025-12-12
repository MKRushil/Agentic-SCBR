<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import { Send } from 'lucide-vue-next'

const chatStore = useChatStore()
const inputText = ref('')

const handleSend = () => {
  if (!inputText.value.trim() || chatStore.isProcessing) return
  chatStore.sendMessage(inputText.value)
  inputText.value = ''
}
</script>

<template>
  <div class="relative p-4 bg-white">
    <textarea 
      id="chatTextarea"
      v-model="inputText"
      placeholder="請輸入病患主訴或回答問題..."
      class="w-full pl-4 pr-12 py-3 border border-slate-200 rounded-lg focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors shadow-sm resize-none text-base leading-relaxed"
      :rows="4"
      maxlength="1000"
      @keydown.enter.prevent="handleSend"
      :disabled="chatStore.isProcessing"
    ></textarea>
    <button 
      @click="handleSend"
      class="absolute right-6 bottom-6 p-2 bg-primary-600 hover:bg-primary-700 text-white rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      :disabled="!inputText.trim() || chatStore.isProcessing"
      title="發送訊息"
    >
      <Send class="w-5 h-5" />
    </button>
  </div>
</template>