<template>
  <view class="page">
    <view class="banner">
      <text class="hello">你好，{{ user.nickname || '微信用户' }}</text>
      <text class="role">{{ roleName }}</text>
    </view>
    <view class="card action" @click="goDetect">
      <text class="action-title">开始检测</text>
      <text class="muted">拍摄或选择水面照片，支持一次最多 9 张</text>
    </view>
    <view class="card" v-if="latest">
      <text class="section">最近一次检测</text>
      <view class="latest" @click="openLatest">
        <image v-if="latest.image" class="thumb" :src="mediaUrl(latest.image)" mode="aspectFill" />
        <view class="info">
          <text class="label" :style="{ color: meta.color }">{{ latest.label_name || '检测失败' }}</text>
          <text class="muted" v-if="latest.status === 'success'">{{ ntuText(latest.ntu) }} NTU · {{ percent(latest.confidence) }}</text>
          <text class="muted" v-else>{{ latest.error_message || '未完成' }}</text>
          <text class="time">{{ latest.created_at }}</text>
        </view>
      </view>
    </view>
    <view class="card" v-else>
      <text class="section">还没有检测记录</text>
      <text class="muted">去拍摄一张水面照片，看看今天的浊度。</text>
    </view>
    <view class="card tips">
      <text class="section">拍摄建议</text>
      <text class="muted">让水面占满画面，避开大面积天空、手指和岸边倒影。</text>
    </view>
  </view>
</template>

<script>
import { ensureLogin, request, currentUser } from '../../utils/request.js'
import { mediaUrl, percent, ntuText, labelMeta } from '../../utils/config.js'

export default {
  data() {
    return { user: {}, latest: null }
  },
  computed: {
    roleName() {
      return this.user.role ? this.user.role.name : '普通用户'
    },
    meta() {
      return labelMeta(this.latest && this.latest.label)
    }
  },
  onShow() {
    if (!ensureLogin()) return
    this.user = currentUser()
    request({ url: '/api/users/me/', silent: true }).then((user) => {
      this.user = user
      uni.setStorageSync('user', user)
    }).catch(() => {})
    request({ url: '/api/detections/records/', data: { page: 1, page_size: 1 }, silent: true }).then((data) => {
      this.latest = data.results && data.results.length ? data.results[0] : null
    }).catch(() => {})
  },
  methods: {
    mediaUrl, percent, ntuText,
    goDetect() {
      uni.switchTab({ url: '/pages/detect/detect' })
    },
    openLatest() {
      if (!this.latest) return
      uni.navigateTo({ url: '/pages/history/detail?id=' + this.latest.id })
    }
  }
}
</script>

<style scoped>
.banner { margin: 24rpx; padding: 36rpx; border-radius: 24rpx; background: #0e7490; color: #fff; }
.hello { display: block; font-size: 40rpx; font-weight: 700; }
.role { display: block; margin-top: 8rpx; opacity: 0.85; }
.action-title { display: block; font-size: 34rpx; font-weight: 700; color: #0e7490; margin-bottom: 8rpx; }
.section { display: block; font-weight: 700; margin-bottom: 16rpx; }
.latest { display: flex; }
.thumb { width: 160rpx; height: 160rpx; border-radius: 16rpx; background: #e2e8f0; }
.info { flex: 1; margin-left: 20rpx; }
.label { display: block; font-size: 32rpx; font-weight: 700; }
.time { display: block; margin-top: 8rpx; color: #94a3b8; font-size: 24rpx; }
.tips .muted { line-height: 1.6; }
</style>
