import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'xhy_access_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))

  const isAuthenticated = computed(() => !!token.value)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem(TOKEN_KEY, t)
  }

  function login(t: string) {
    setToken(t)
  }

  function logout() {
    token.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return { token, isAuthenticated, login, logout }
})