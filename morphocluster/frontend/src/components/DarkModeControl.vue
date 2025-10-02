<template>
    <button
        @click="toggleDarkMode"
        class="dark-mode-toggle"
        :title="dark_mode ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
    >
        <i v-if="dark_mode" class="mdi mdi-moon-waning-crescent" key="moon"></i>
        <i v-else class="mdi mdi-weather-sunny" key="sun"></i>
    </button>
</template>

<script>
export default {
    name: "dark-mode-toggle",
    data() {
        // Initialize dark mode state immediately, before component is mounted
        const savedMode = typeof window !== 'undefined' && localStorage.getItem("dark-mode") === "true";
        console.log("[DarkModeControl] Initializing with dark_mode:", savedMode);
        return {
            dark_mode: savedMode
        };
    },
    mounted() {
        console.log("[DarkModeControl] Mounted with dark_mode:", this.dark_mode);
        // Apply dark mode state when component is mounted
        this.applyDarkMode(this.dark_mode);
        // Force a re-render to ensure icon is visible
        this.$forceUpdate();
    },
    methods: {
        toggleDarkMode() {
            this.dark_mode = !this.dark_mode;
            console.log("[DarkModeControl] Toggled to:", this.dark_mode);
            localStorage.setItem("dark-mode", this.dark_mode ? "true" : "false");
            this.applyDarkMode(this.dark_mode);
        },
        applyDarkMode(isDark) {
            if (isDark) {
                document.documentElement.classList.add("dark-mode");
            } else {
                document.documentElement.classList.remove("dark-mode");
            }
        }
    }
};
</script>

<style scoped>
.dark-mode-toggle {
    background: none;
    border: none;
    color: #ffffff;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    line-height: 1;
}

.dark-mode-toggle:hover {
    opacity: 0.8;
    transform: scale(1.1);
}

.dark-mode-toggle:active {
    transform: scale(0.95);
}

.dark-mode-toggle i {
    transition: transform 0.3s ease;
    color: #ffffff;
}

.dark-mode-toggle:hover i {
    transform: rotate(20deg);
}
</style>
