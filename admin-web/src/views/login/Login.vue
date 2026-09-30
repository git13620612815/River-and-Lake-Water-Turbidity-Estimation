<template>
  <div class="login-page">
    <section class="intro">
      <div class="mark">浊</div>
      <p class="eyebrow">河湖水质 · 管理端</p>
      <h1>浊度估算后台</h1>
      <p class="lead">维护用户与权限，整理训练图片，并查看每次检测的等级和浊度估算。</p>
      <ul>
        <li>概览用户、检测量和数据集</li>
        <li>按等级管理训练图片</li>
        <li>查阅全部预测记录</li>
      </ul>
    </section>
    <section class="panel">
      <el-card class="card" shadow="never">
        <h2>登录</h2>
        <p class="hint">请使用管理员账号。微信用户请打开小程序。</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" size="large" placeholder="请输入用户名" autocomplete="username" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              show-password
              placeholder="请输入密码"
              autocomplete="current-password"
              @keyup.enter="submit"
            />
          </el-form-item>
          <el-button class="full" type="primary" size="large" :loading="loading" @click="submit">进入管理端</el-button>
        </el-form>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import http from '../../api/http'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const data = await http.post('/api/admin/auth/login/', form)
    localStorage.setItem('admin_access', data.access)
    localStorage.setItem('admin_refresh', data.refresh)
    localStorage.setItem('admin_user', JSON.stringify(data.user))
    router.push('/dashboard')
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(320px, 1.1fr) minmax(360px, 0.9fr);
  background: #f4f8fa;
}
.intro {
  position: relative;
  overflow: hidden;
  padding: 72px 64px;
  color: #f4fbfd;
  background:
    linear-gradient(180deg, rgba(6, 24, 32, 0.28) 0%, rgba(6, 24, 32, 0.46) 48%, rgba(6, 24, 32, 0.72) 100%),
    url("../../assets/login-lake.png") center / cover no-repeat;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.intro::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(6, 24, 32, 0.18), transparent 42%);
  pointer-events: none;
}
.mark,
.eyebrow,
h1,
.lead,
ul {
  position: relative;
  z-index: 1;
}
.mark {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
  font-size: 22px;
  font-weight: 700;
  backdrop-filter: blur(8px);
}
.eyebrow {
  margin: 28px 0 8px;
  letter-spacing: 0.12em;
  font-size: 13px;
  color: #b7e4ee;
}
h1 {
  margin: 0;
  font-size: 40px;
  line-height: 1.2;
}
.lead {
  max-width: 460px;
  margin: 16px 0 0;
  color: #d5eef4;
  line-height: 1.7;
}
ul {
  margin: 32px 0 0;
  padding: 0;
  list-style: none;
}
li {
  position: relative;
  margin-top: 12px;
  padding-left: 18px;
  color: #e7f7fb;
}
li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.55em;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #7dd3e8;
}
.panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
}
.card {
  width: min(400px, 100%);
  border: none;
  border-radius: 18px;
  box-shadow: 0 18px 50px rgba(15, 61, 76, 0.08);
}
h2 {
  margin: 0;
  font-size: 26px;
  color: #0f3d4c;
}
.hint {
  margin: 8px 0 22px;
  color: #64748b;
  line-height: 1.6;
}
.full {
  width: 100%;
  margin-top: 6px;
}
@media (max-width: 860px) {
  .login-page { grid-template-columns: 1fr; }
  .intro { padding: 40px 28px 32px; }
  h1 { font-size: 30px; }
  ul { display: none; }
}
</style>
