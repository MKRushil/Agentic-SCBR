<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chatStore'
import { scbrService } from '@/api/scbrService'
import { ThumbsUp, Edit, ThumbsDown, Check } from 'lucide-vue-next'

const chatStore = useChatStore()
const isSubmitted = ref(false)
const feedbackStatus = ref('')

const sendFeedback = async (action: 'ACCEPT' | 'MODIFY' | 'REJECT') => {
  if (isSubmitted.value) return

  try {
    await scbrService.sendFeedback({
      session_id: chatStore.sessionId,
      action: action
    })
    isSubmitted.value = true
    feedbackStatus.value = action === 'ACCEPT' ? '已採納並寫入案例庫' : 
                           action === 'REJECT' ? '已拒絕並標記' : '已進入修改模式'
  } catch (e) {
    alert('回饋發送失敗')
  }
}
</script>

<template>
  <div v-if="chatStore.currentDiagnosis.length > 0 && !isSubmitted" class="flex justify-end space-x-2 mt-4 pt-4 border-t border-slate-200">
    <button 
      @click="sendFeedback('ACCEPT')"
      class="flex items-center px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200 text-xs transition"
    >
      <ThumbsUp class="w-3 h-3 mr-1" /> 採納
    </button>
    <button 
      @click="sendFeedback('MODIFY')"
      class="flex items-center px-3 py-1.5 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-xs transition"
    >
      <Edit class="w-3 h-3 mr-1" /> 修改
    </button>
    <button 
      @click="sendFeedback('REJECT')"
      class="flex items-center px-3 py-1.5 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-xs transition"
    >
      <ThumbsDown class="w-3 h-3 mr-1" /> 拒絕
    </button>
  </div>
  
  <div v-else-if="isSubmitted" class="mt-4 pt-2 text-right text-xs text-slate-500 flex justify-end items-center">
    <Check class="w-3 h-3 mr-1 text-emerald-500" />
    {{ feedbackStatus }}
  </div>
</template>