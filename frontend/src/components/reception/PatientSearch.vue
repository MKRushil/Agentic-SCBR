<script setup lang="ts">
import { ref } from 'vue'
import { usePatientStore } from '@/stores/patientStore'
import { Search, LogOut, User } from 'lucide-vue-next'

const patientStore = usePatientStore()
const inputId = ref('')

const handleLogin = () => {
  if (inputId.value.trim().length >= 4) {
    patientStore.setPatient(inputId.value)
    inputId.value = '' // Clear input after search
  }
}
</script>

<template>
  <div class="flex items-center">
    <div v-if="patientStore.isIdentified" class="flex items-center text-sm">
        <User class="w-4 h-4 text-slate-500 mr-2" />
        <span class="text-slate-600">病患: <strong class="text-slate-900">{{ patientStore.patientName }}</strong></span>
        <span class="text-slate-400 text-xs border-l pl-3 border-slate-300 ml-3">ID: {{ patientStore.currentPatientId }}</span>
        <button @click="patientStore.clearPatient" class="ml-4 text-red-500 hover:bg-red-50 px-2 py-0.5 rounded transition flex items-center">
          <LogOut class="w-3 h-3 mr-1" /> 登出
        </button>
    </div>
    <div v-else class="flex items-center bg-white border border-slate-200 rounded-lg overflow-hidden focus-within:border-primary-500 transition-all shadow-sm">
      <input 
        id="idInput"
        v-model="inputId"
        type="text" 
        placeholder="請輸入 ID 調閱病歷..."
        class="px-4 py-2 text-sm focus:outline-none flex-grow"
        @keyup.enter="handleLogin"
      />
      <button 
        @click="handleLogin"
        class="bg-slate-50 text-slate-500 hover:bg-primary-50 hover:text-primary-700 px-3 py-2 transition-colors border-l border-slate-200"
        title="調閱病歷"
      >
        <Search class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>