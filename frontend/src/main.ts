import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css' // 假設 Tailwind 已經設定在 style.css
import App from './App.vue'

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.mount('#app')

console.log(`[System] SCBR-CDSS Frontend v8.0 Started.`)