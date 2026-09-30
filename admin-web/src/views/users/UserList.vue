<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-input v-model="query.nickname" placeholder="昵称" clearable style="width: 180px" />
      <el-select v-model="query.role" clearable placeholder="角色" style="width: 140px">
        <el-option v-for="item in roles" :key="item.id" :label="item.name" :value="item.code" />
      </el-select>
      <el-select v-model="query.is_active" clearable placeholder="状态" style="width: 120px">
        <el-option label="启用" value="1" />
        <el-option label="停用" value="0" />
      </el-select>
      <el-button type="primary" @click="load(1)">查询</el-button>
      <el-button @click="openCreate">新增用户</el-button>
    </div>
    <el-table :data="rows" border>
      <el-table-column prop="nickname" label="昵称" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="openid_masked" label="openid" />
      <el-table-column label="角色"><template #default="{ row }">{{ row.role ? row.role.name : '' }}</template></el-table-column>
      <el-table-column prop="phone" label="手机号" />
      <el-table-column label="状态"><template #default="{ row }">{{ row.is_active ? '启用' : '停用' }}</template></el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="170" />
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link @click="goRecords(row)">检测记录</el-button>
          <el-button link type="danger" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination class="pager" layout="prev, pager, next" :total="total" :page-size="10" @current-change="load" />
    <el-dialog v-model="visible" :title="editing ? '编辑用户' : '新增用户'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="昵称"><el-input v-model="form.nickname" /></el-form-item>
        <el-form-item label="openid"><el-input v-model="form.openid" placeholder="小程序账号可填" /></el-form-item>
        <el-form-item label="用户名"><el-input v-model="form.username" placeholder="后台登录名" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password placeholder="新建必填，编辑时留空则不改" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_id" style="width: 100%">
            <el-option v-for="item in roles" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editing" label="启用"><el-switch v-model="form.is_active" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '../../api/http'

const router = useRouter()
const roles = ref([])
const rows = ref([])
const total = ref(0)
const visible = ref(false)
const editing = ref(false)
const query = reactive({ nickname: '', role: '', is_active: '' })
const form = reactive({ id: null, nickname: '', openid: '', username: '', password: '', phone: '', role_id: null, is_active: true })

async function loadRoles() {
  roles.value = await http.get('/api/admin/roles/')
}

async function load(page = 1) {
  const data = await http.get('/api/admin/users/', { params: { ...query, page, page_size: 10 } })
  rows.value = data.results
  total.value = data.count
}

function openCreate() {
  editing.value = false
  Object.assign(form, { id: null, nickname: '', openid: '', username: '', password: '', phone: '', role_id: roles.value[0] && roles.value[0].id, is_active: true })
  visible.value = true
}

function openEdit(row) {
  editing.value = true
  Object.assign(form, {
    id: row.id,
    nickname: row.nickname,
    openid: '',
    username: row.username,
    password: '',
    phone: row.phone,
    role_id: row.role && row.role.id,
    is_active: row.is_active
  })
  visible.value = true
}

async function save() {
  try {
    if (editing.value) {
      const payload = { nickname: form.nickname, username: form.username, phone: form.phone, role_id: form.role_id, is_active: form.is_active }
      if (form.password) payload.password = form.password
      if (form.openid) payload.openid = form.openid
      await http.patch(`/api/admin/users/${form.id}/`, payload)
    } else {
      await http.post('/api/admin/users/', form)
    }
    visible.value = false
    ElMessage.success('已保存')
    load()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm('删除后将同时删除该用户的预测图片，建议先停用。确定删除？', '删除用户')
    await http.delete(`/api/admin/users/${row.id}/`)
    load()
  } catch (error) {
    if (error !== 'cancel' && error.message) ElMessage.error(error.message)
  }
}

function goRecords(row) {
  router.push({ path: '/records', query: { user_id: row.id } })
}

onMounted(async () => {
  try {
    await loadRoles()
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  }
})
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
.pager { margin-top: 12px; justify-content: flex-end; }
</style>
