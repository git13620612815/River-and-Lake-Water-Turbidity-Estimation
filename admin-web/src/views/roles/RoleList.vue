<template>
  <div>
    <el-card shadow="never" class="block">
      <el-form inline>
        <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="form.code" placeholder="如 labeler" /></el-form-item>
        <el-button type="primary" @click="createRole">新增角色</el-button>
      </el-form>
    </el-card>
    <el-card v-for="role in roles" :key="role.id" shadow="never" class="block">
      <div class="title">{{ role.name }} <span class="muted">{{ role.code }}{{ role.is_builtin ? ' · 内置' : '' }}</span></div>
      <el-checkbox-group v-model="draft[role.id]">
        <el-checkbox v-for="item in permissions" :key="item.id" :value="item.id">{{ item.name }}</el-checkbox>
      </el-checkbox-group>
      <div class="ops">
        <el-button type="primary" @click="save(role)">保存权限</el-button>
        <el-button v-if="!role.is_builtin" type="danger" plain @click="remove(role)">删除</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../../api/http'

const permissions = ref([])
const roles = ref([])
const draft = reactive({})
const form = reactive({ name: '', code: '' })

async function load() {
  permissions.value = await http.get('/api/admin/permissions/')
  roles.value = await http.get('/api/admin/roles/')
  roles.value.forEach((role) => { draft[role.id] = role.permission_ids.slice() })
}

async function save(role) {
  try {
    await http.patch(`/api/admin/roles/${role.id}/`, { name: role.name, permission_ids: draft[role.id] || [] })
    ElMessage.success('已保存')
    const user = await http.get('/api/users/me/')
    localStorage.setItem('admin_user', JSON.stringify(user))
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function createRole() {
  const dataset = permissions.value.find((item) => item.code === 'dataset.manage')
  try {
    await http.post('/api/admin/roles/', { name: form.name, code: form.code, permission_ids: dataset ? [dataset.id] : [] })
    form.name = ''
    form.code = ''
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function remove(role) {
  try {
    await ElMessageBox.confirm('仅无人使用的自定义角色可以删除', '删除角色')
    await http.delete(`/api/admin/roles/${role.id}/`)
    await load()
  } catch (error) {
    if (error !== 'cancel' && error.message) ElMessage.error(error.message)
  }
}

onMounted(() => load().catch((error) => ElMessage.error(error.message)))
</script>

<style scoped>
.block { margin-bottom: 16px; }
.title { font-weight: 700; margin-bottom: 12px; }
.muted { color: #64748b; font-weight: 400; }
.ops { margin-top: 12px; }
</style>
