<template>
  <view class="page">
    <view class="hero">
      <text class="title">河湖水质浊度估算</text>
      <text class="sub">拍摄水面照片，估算浊度等级与 NTU</text>
    </view>
    <view class="panel">
      <view class="tabs">
        <text :class="['tab', mode === 'login' ? 'on' : '']" @click="mode = 'login'">登录</text>
        <text :class="['tab', mode === 'register' ? 'on' : '']" @click="mode = 'register'">注册</text>
      </view>
      <input class="field" v-model="form.username" maxlength="20" placeholder="用户名，3 到 20 位" />
      <input v-if="mode === 'register'" class="field" v-model="form.nickname" maxlength="64" placeholder="昵称，可不填" />
      <input class="field" password v-model="form.password" maxlength="32" placeholder="密码，至少 6 位" />
      <input v-if="mode === 'register'" class="field" password v-model="form.confirm" maxlength="32" placeholder="再次输入密码" />
      <button class="primary-btn btn" :disabled="loading" @click="submit">{{ mode === 'login' ? '登录' : '注册并进入' }}</button>
      <text class="hint">{{ mode === 'login' ? '没有账号时切换到注册。管理员后台请用电脑浏览器打开。' : '注册后成为普通用户，可拍照检测和查看自己的记录。' }}</text>
    </view>
  </view>
</template>

<script>
import { request, saveSession } from '../../utils/request.js'

export default {
  data() {
    return {
      mode: 'login',
      loading: false,
      form: { username: '', nickname: '', password: '', confirm: '' }
    }
  },
  onLoad() {
    if (uni.getStorageSync('access')) {
      uni.switchTab({ url: '/pages/home/home' })
    }
  },
  methods: {
    submit() {
      if (this.loading) return
      const username = (this.form.username || '').trim()
      const password = this.form.password || ''
      if (!username || !password) {
        uni.showToast({ title: '请填写用户名和密码', icon: 'none' })
        return
      }
      if (this.mode === 'register') {
        if (password.length < 6) {
          uni.showToast({ title: '密码至少 6 位', icon: 'none' })
          return
        }
        if (password !== this.form.confirm) {
          uni.showToast({ title: '两次密码不一致', icon: 'none' })
          return
        }
      }
      const url = this.mode === 'register' ? '/api/auth/register/' : '/api/auth/login/'
      const data = { username, password }
      if (this.mode === 'register' && (this.form.nickname || '').trim()) {
        data.nickname = this.form.nickname.trim()
      }
      this.loading = true
      request({ url, method: 'POST', data }).then((payload) => {
        saveSession(payload)
        uni.switchTab({ url: '/pages/home/home' })
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>

<style scoped>
.page { min-height: 100vh; background: linear-gradient(180deg, #0e7490 0%, #e0f2fe 42%, #f3f7fb 42%); }
.hero { padding: 120rpx 48rpx 64rpx; color: #ffffff; }
.title { display: block; font-size: 48rpx; font-weight: 700; }
.sub { display: block; margin-top: 16rpx; font-size: 26rpx; opacity: 0.9; }
.panel { margin: 0 32rpx; background: #fff; border-radius: 28rpx; padding: 36rpx 36rpx 48rpx; }
.tabs { display: flex; margin-bottom: 12rpx; }
.tab { flex: 1; text-align: center; padding: 16rpx 0 20rpx; color: #64748b; font-size: 30rpx; }
.tab.on { color: #0e7490; font-weight: 700; border-bottom: 4rpx solid #0e7490; }
.field {
  margin-top: 24rpx;
  height: 88rpx;
  padding: 0 28rpx;
  background: #f8fafc;
  border-radius: 16rpx;
  font-size: 28rpx;
}
.btn { margin-top: 36rpx; }
.hint { display: block; margin-top: 28rpx; color: #64748b; font-size: 24rpx; line-height: 1.6; }
</style>
