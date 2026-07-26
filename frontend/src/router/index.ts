import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',  // beforeEach guard will redirect to /chat if authenticated
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/login')
  } else if (to.meta.guest && auth.isAuthenticated) {
    next('/chat')
  } else {
    next()
  }
})

export default router