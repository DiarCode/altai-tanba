import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './styles.css'

import App from './App.vue'
import router from './router'
import { MotionPlugin } from '@vueuse/motion'
import { VueQueryPlugin } from '@tanstack/vue-query'

const app = createApp(App)

app.use(createPinia())
app.use(VueQueryPlugin)
app.use(router)
app.use(MotionPlugin)

app.mount('#app')
