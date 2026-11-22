import { createRouter, createWebHistory } from 'vue-router'

import PageHome from '@/pages/PageHome.vue'
import PageCampaigns from '@/pages/PageCampaigns.vue'
import PageEditor from '@/pages/PageEditor.vue'
import PageNotFound from '@/pages/PageNotFound.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home', // создание кампании
      component: PageHome,
    },
    {
      path: '/campaigns',
      name: 'campaigns', // список кампаний Keitaro
      component: PageCampaigns,
    },
    {
      path: '/campaigns/:id(\\d+)',
      name: 'editor', // редактор выбранной кампании
      component: PageEditor,
    },
    {
      path: '/:pathMatch(.*)*', // 404
      name: 'not-found',
      component: PageNotFound,
    },
  ],
})

export default router
