<template>
  <el-container class="shell">
    <el-aside width="220px" class="aside">
      <div class="brand">河湖水质管理</div>
      <el-menu :default-active="route.path" router background-color="#0f3d4c" text-color="#d7eef3" active-text-color="#ffffff">
        <el-menu-item v-if="allowed('dashboard.view')" index="/dashboard">概览</el-menu-item>
        <el-menu-item v-if="allowed('user.manage')" index="/users">用户管理</el-menu-item>
        <el-menu-item v-if="allowed('role.manage')" index="/roles">角色权限</el-menu-item>
        <el-menu-item v-if="allowed('dataset.manage')" index="/dataset">数据集</el-menu-item>
        <el-menu-item v-if="allowed('record.view')" index="/records">预测记录</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span>{{ route.meta.title || '管理端' }}</span>
        <div class="account">
          <span>{{ user.nickname || user.username }}</span>
          <el-button link type="primary" @click="passwordVisible = true">修改密码</el-button>
          <el-button link type="danger" @click="logout">退出</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
    <el-dialog v-model="passwordVisible" title="修改密码" width="420px">
      <el-form label-width="90px">
        <el-form-item label="原密码"><el-input v-model="passwordForm.old_password" type="password" show-password /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="passwordForm.new_password" type="password" show-password /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordVisible = false">取消</el-button>
        <el-button type="primary" @click="savePassword">保存</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http, { currentUser, hasPerm } from '../api/http'

const route = useRoute()
const router = useRouter()
const user = computed(() => currentUser())
const passwordVisible = ref(false)
const passwordForm = reactive({ old_password: '', new_password: '' })

function allowed(code) {
  return hasPerm(code)
}

function logout() {
  localStorage.removeItem('admin_access')
  localStorage.removeItem('admin_refresh')
  localStorage.removeItem('admin_user')
  router.push('/login')
}

async function savePassword() {
  try {
    await http.post('/api/admin/auth/password/', passwordForm)
    ElMessage.success('密码已更新')
    passwordVisible.value = false
    passwordForm.old_password = ''
    passwordForm.new_password = ''
  } catch (error) {
    ElMessage.error(error.message)
  }
}
</script>

<style scoped>
.shell { min-height: 100vh; }
.aside { background: #0f3d4c; }
.brand { color: #fff; font-size: 18px; font-weight: 700; padding: 22px 20px; }
.header { display: flex; align-items: center; justify-content: space-between; background: #fff; border-bottom: 1px solid #e6eef2; }
.account { display: flex; align-items: center; gap: 12px; }
.main { background: #f3f7fb; }
</style>
