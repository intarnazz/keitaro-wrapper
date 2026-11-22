import { createRouter, createWebHistory } from 'vue-router'

import PageHome from '@/pages/PageHome.vue'
import PageNotFound from '@/pages/PageNotFound.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: PageHome,
    },
    {
      path: '/:pathMatch(.*)*', // 404
      name: 'not-found',
      component: PageNotFound,
    },
  ],
})

export default router
