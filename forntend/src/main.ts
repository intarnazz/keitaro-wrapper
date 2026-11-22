import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'nprogress/nprogress.css'
import '@/assets/css/root.css'
import '@/assets/css/loader.css'
import '@/assets/sass/style.sass'
import '@/assets/css/tailwind.css'

const app = createApp(App)

app.use(router)

app.mount('#app')
