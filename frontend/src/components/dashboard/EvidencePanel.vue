<script setup lang="ts">
import { useChatStore } from '@/stores/chatStore'
import { FileText, Activity } from 'lucide-vue-next'
import { marked } from 'marked' // 用於渲染 Markdown 報告

const chatStore = useChatStore()
</script>

<template>
  <div class="space-y-4">
    <!-- 1. 推導證據 (Evidence Trace) -->
    <div class="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
      <h3 class="flex items-center text-sm font-bold text-slate-700 mb-2 border-l-4 border-blue-500 pl-2">
        <Activity class="w-4 h-4 mr-2 text-blue-500" />
        病機推導過程 (Evidence Trace)
      </h3>
      <p class="text-sm text-slate-600 leading-relaxed whitespace-pre-line bg-slate-50 p-3 rounded">
        {{ chatStore.evidenceTrace || '等待輸入症狀以啟動推導...' }}
      </p>
    </div>

    <!-- 2. 詳細報告 (Formatted Report) -->
    <div v-if="chatStore.formattedReport" class="bg-white p-4 rounded-lg shadow-sm border border-slate-200">
      <h3 class="flex items-center text-sm font-bold text-slate-700 mb-2 border-l-4 border-purple-500 pl-2">
        <FileText class="w-4 h-4 mr-2 text-purple-500" />
        結構化診斷報告
      </h3>
      <div 
        class="prose prose-sm prose-slate max-w-none bg-slate-50 p-4 rounded border border-slate-100"
        v-html="marked.parse(chatStore.formattedReport)"
      ></div>
    </div>
  </div>
</template>