<script setup lang="ts">
import { usePatientStore } from '@/stores/patientStore'
import { useChatStore } from '@/stores/chatStore'

// Components
import PatientSearch from '@/components/reception/PatientSearch.vue'
import ChatContainer from '@/components/chat/ChatContainer.vue'
import InputArea from '@/components/chat/InputArea.vue'
import DiagnosisCard from '@/components/dashboard/DiagnosisCard.vue'
import EvidencePanel from '@/components/dashboard/EvidencePanel.vue'
import RadarChart from '@/components/dashboard/RadarChart.vue'
import FeedbackActions from '@/components/interaction/FeedbackActions.vue'
import SafetyBanner from '@/components/layout/SafetyBanner.vue'
import GlobalDisclaimer from '@/components/layout/GlobalDisclaimer.vue'

const patientStore = usePatientStore()
const chatStore = useChatStore()
</script>

<template>
  <div class="h-screen flex flex-col font-sans text-slate-800 bg-gray-100">
    <!-- Header -->
    <header class="bg-emerald-700 text-white p-4 shadow-md flex justify-between items-center z-10">
      <div class="flex items-center space-x-3">
        <h1 class="text-xl font-bold tracking-wide">Agentic SCBR-CDSS</h1>
        <span class="text-xs bg-emerald-800 px-2 py-1 rounded border border-emerald-600">v8.0</span>
      </div>
      <div v-if="patientStore.isIdentified" class="flex items-center space-x-4 text-sm">
        <span>病患: <strong class="text-yellow-300">{{ patientStore.patientName }}</strong></span>
        <span>ID: {{ patientStore.currentPatientId }}</span>
        <button @click="patientStore.clearPatient" class="text-emerald-200 hover:text-white underline">登出</button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 flex overflow-hidden">
      
      <!-- 1. Reception Mode (未登入) -->
      <div v-if="!patientStore.isIdentified" class="flex-1 flex items-center justify-center bg-gray-50">
        <div class="w-full max-w-md p-8 bg-white rounded-xl shadow-lg border border-slate-200 text-center">
          <h2 class="text-2xl font-bold text-slate-700 mb-6">病患報到系統</h2>
          <PatientSearch />
          <p class="mt-4 text-xs text-slate-400">請輸入身分證字號或病歷號以啟動診斷工作流。</p>
        </div>
      </div>

      <!-- 2. Clinical Mode (已登入) -->
      <div v-else class="flex w-full h-full">
        
        <!-- Left Column: Chat Interaction -->
        <div class="w-1/2 flex flex-col border-r border-slate-200 bg-white relative">
          <SafetyBanner />
          <ChatContainer />
          <InputArea />
        </div>

        <!-- Right Column: Dashboard & Evidence -->
        <div class="w-1/2 flex flex-col overflow-y-auto bg-slate-50 p-6 space-y-6">
          
          <!-- Diagnosis Cards -->
          <section>
            <h3 class="text-sm font-bold text-slate-500 uppercase tracking-wider mb-3">診斷建議 (Suggestions)</h3>
            <div v-if="chatStore.currentDiagnosis.length === 0" class="text-slate-400 text-sm italic text-center py-8 bg-slate-100 rounded border border-dashed border-slate-300">
              尚無診斷結果，請在左側輸入病患資訊。
            </div>
            
            <DiagnosisCard 
              v-for="diag in chatStore.currentDiagnosis"
              :key="diag.disease_name"
              :diagnosis="diag"
              :mode="chatStore.responseType"
            />

            <!-- Learning Loop -->
            <FeedbackActions />
          </section>

          <!-- Visualization -->
          <RadarChart />

          <!-- Evidence Trace -->
          <EvidencePanel />
        </div>

      </div>
    </main>

    <!-- Footer Disclaimer -->
    <GlobalDisclaimer />
  </div>
</template>