import HomePage from '@/modules/home/pages/home-page.vue'
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', component: HomePage },
    { path: '/sessions/:id', component: () => import('@/modules/session/pages/session.vue') },
    {
      path: '/sessions/:id/documents/:documentId',
      component: () => import('@/modules/document/document-page.vue'),
    },
  ],
})

export default router
