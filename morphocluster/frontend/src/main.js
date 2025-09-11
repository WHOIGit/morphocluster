import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Bootstrap Vue 3
import BootstrapVueNext from 'bootstrap-vue-next'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue-next/dist/bootstrap-vue-next.css'

// Custom styles
import './assets/styles.css'

const app = createApp(App)

app.use(router)
app.use(BootstrapVueNext)

// Make config available globally
app.provide('config', window.config)

// Initialize dark mode on app start
const darkMode = localStorage.getItem("dark-mode") === "true";
if (darkMode) {
    document.documentElement.classList.add("dark-mode");
} else {
    document.documentElement.classList.remove("dark-mode");
}

app.mount('#app')
