import { createRouter, createWebHistory } from 'vue-router'
import http, { hasPerm } from '../api/http'
import AdminLayout from '../layout/AdminLayout.vue'
import Login from '../views/login/Login.vue'
import Dashboard from '../views/dashboard/Dashboard.vue'
import UserList from '../views/users/UserList.vue'
import RoleList from '../views/roles/RoleList.vue'
import DatasetList from '../views/dataset/DatasetList.vue'
import RecordList from '../views/records/RecordList.vue'

const ADMIN_PERMS = ['dashboard.view', 'user.manage', 'role.manage', 'dataset.manage']

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login },
    {
      path: '/',
      component: AdminLayout,
      redirect: '/dashboard',
      children: [
        { path: 'dashboard', component: Dashboard, meta: { perm: 'dashboard.view', title: '概览' } },
        { path: 'users', component: UserList, meta: { perm: 'user.manage', title: '用户管理' } },
        { path: 'roles', component: RoleList, meta: { perm: 'role.manage', title: '角色权限' } },
        { path: 'dataset', component: DatasetList, meta: { perm: 'dataset.manage', title: '数据集' } },
        { path: 'records', component: RecordList, meta: { perm: 'record.view', title: '预测记录' } }
      ]
    }
  ]
})

function firstPage(permissions) {
  const found = router.getRoutes().find((item) => item.meta.perm && permissions.includes(item.meta.perm))
  return found ? found.path : '/login'
}

router.beforeEach(async (to) => {
  if (to.path === '/login') return true
  if (!localStorage.getItem('admin_access')) return '/login'
  try {
    const user = await http.get('/api/users/me/')
    localStorage.setItem('admin_user', JSON.stringify(user))
    const permissions = user.permissions || []
    if (!ADMIN_PERMS.some((code) => permissions.includes(code))) {
      localStorage.removeItem('admin_access')
      return '/login'
    }
    if (to.meta.perm && !permissions.includes(to.meta.perm)) return firstPage(permissions)
    return true
  } catch (error) {
    if (!localStorage.getItem('admin_access')) return '/login'
    return true
  }
})

export { hasPerm }
export default router
