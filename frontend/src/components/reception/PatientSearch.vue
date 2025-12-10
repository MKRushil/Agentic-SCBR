<script setup lang="ts">
import { ref } from 'vue'
import { usePatientStore } from '@/stores/patientStore'
import { UserCheck } from 'lucide-vue-next'

const patientStore = usePatientStore()
const inputId = ref('')

const handleLogin = () => {
  if (inputId.value.trim().length >= 4) {
    patientStore.setPatient(inputId.value)
  }
}
</script>

<template>
  <div class="flex items-center space-x-2 bg-white p-2 rounded-lg shadow-sm border border-slate-200">
    <div class="relative flex-grow">
      <input 
        v-model="inputId"
        type="text" 
        placeholder="請輸入病患身分證字號或病歷號..."
        class="w-full pl-3 pr-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
        @keyup.enter="handleLogin"
      />
    </div>
    <button 
      @click="handleLogin"
      class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-md text-sm flex items-center transition"
    >
      <UserCheck class="w-4 h-4 mr-1" />
      調閱
    </button>
  </div>
</template>