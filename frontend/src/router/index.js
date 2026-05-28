import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Accounts from '../views/Accounts.vue'
import Tasks from '../views/Tasks.vue'
import Scheduler from '../views/Scheduler.vue'
import Logs from '../views/Logs.vue'
import Recap from '../views/Recap.vue'
import Contributor from '../views/Contributor.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: Dashboard },
  { path: '/manager', component: Tasks },
  { path: '/accounts', component: Accounts },
  { path: '/links', component: Scheduler },
  { path: '/recap', component: Recap },
  { path: '/logs', component: Logs },
  { path: '/contributor', component: Contributor },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})
export default router
