<template>
  <view>
    <view class="card profile">
      <image class="avatar" :src="avatarSrc" mode="aspectFill" @click="changeAvatar" />
      <view>
        <text class="name">{{ form.nickname || '微信用户' }}</text>
        <text class="muted">{{ roleName }}</text>
      </view>
    </view>
    <view class="card">
      <text class="label">昵称</text>
      <input class="input" v-model="form.nickname" maxlength="64" placeholder="请输入昵称" />
      <text class="label">联系方式</text>
      <input class="input" v-model="form.phone" maxlength="11" type="number" placeholder="手机号，可不填" />
      <button class="primary-btn" @click="save">保存</button>
    </view>
    <button class="logout" @click="logout">退出登录</button>
  </view>
</template>

<script>
import { ensureLogin, request, upload, currentUser, clearAuth } from '../../utils/request.js'
import { mediaUrl } from '../../utils/config.js'

export default {
  data() {
    return { form: { nickname: '', phone: '', avatar: '' }, roleName: '' }
  },
  computed: {
    avatarSrc() {
      return this.form.avatar ? mediaUrl(this.form.avatar) : '/static/avatar.png'
    }
  },
  onShow() {
    if (!ensureLogin()) return
    const cached = currentUser()
    this.fill(cached)
    request({ url: '/api/users/me/' }).then((user) => {
      uni.setStorageSync('user', user)
      this.fill(user)
    })
  },
  methods: {
    fill(user) {
      this.form = {
        nickname: user.nickname || '',
        phone: user.phone || '',
        avatar: user.avatar || ''
      }
      this.roleName = user.role ? user.role.name : ''
    },
    changeAvatar() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          upload({ url: '/api/users/me/avatar/', filePath: res.tempFilePaths[0] }).then((user) => {
            uni.setStorageSync('user', user)
            this.fill(user)
          })
        }
      })
    },
    save() {
      request({
        url: '/api/users/me/',
        method: 'PATCH',
        data: { nickname: this.form.nickname, phone: this.form.phone }
      }).then((user) => {
        uni.setStorageSync('user', user)
        this.fill(user)
        uni.showToast({ title: '已保存', icon: 'success' })
      })
    },
    logout() {
      clearAuth()
      uni.reLaunch({ url: '/pages/login/login' })
    }
  }
}
</script>

<style scoped>
.profile { display: flex; align-items: center; }
.avatar { width: 120rpx; height: 120rpx; border-radius: 60rpx; background: #cffafe; margin-right: 20rpx; }
.name { display: block; font-size: 34rpx; font-weight: 700; }
.label { display: block; margin: 12rpx 0; color: #475569; }
.input { background: #f8fafc; border-radius: 12rpx; padding: 18rpx; margin-bottom: 12rpx; }
.menu { padding: 22rpx 0; border-bottom: 1rpx solid #f1f5f9; color: #0e7490; }
.logout { margin: 24rpx; background: #fff; color: #dc2626; border-radius: 999rpx; }
</style>
