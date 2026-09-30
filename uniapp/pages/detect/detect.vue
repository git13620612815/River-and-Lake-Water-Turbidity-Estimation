<template>
  <view class="page">
    <view class="card">
      <text class="title">选择水面照片</text>
      <text class="muted">相册或相机，单次最多 9 张。系统会压缩后逐张上传，再进行预处理和分类。</text>
      <button class="primary-btn pick" :disabled="submitting" @click="choose">选择图片</button>
      <view class="grid" v-if="files.length">
        <image v-for="(item, index) in files" :key="index" :src="item" mode="aspectFill" class="shot" @click="preview(index)" />
      </view>
      <button class="primary-btn pick" :disabled="submitting || !files.length" @click="start">
        {{ submitting ? '处理中…' : '开始检测' }}
      </button>
    </view>
    <view class="card" v-if="items.length">
      <text class="title">处理进度 {{ finished }}/{{ items.length }}</text>
      <view v-for="(item, index) in items" :key="index" class="line">
        <text>第 {{ index + 1 }} 张</text>
        <text class="state">{{ statusText(item) }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { ensureLogin, request, upload, compressImage, hasPerm } from '../../utils/request.js'

const STATUS = {
  waiting: '等待上传',
  uploading: '上传中',
  pending: '等待推理',
  preprocessing: '预处理',
  inferring: '模型推理',
  success: '完成',
  failed: '失败'
}

export default {
  data() {
    return { files: [], items: [], submitting: false, finished: 0 }
  },
  onShow() {
    ensureLogin()
  },
  methods: {
    choose() {
      if (this.submitting) return
      uni.chooseImage({
        count: 9,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          this.files = res.tempFilePaths.slice(0, 9)
          this.items = []
        }
      })
    },
    preview(index) {
      uni.previewImage({ current: this.files[index], urls: this.files })
    },
    statusText(item) {
      if (item.status === 'uploading') return '上传中 ' + item.progress + '%'
      if (item.status === 'failed') return item.error || '失败'
      return STATUS[item.status] || item.status
    },
    async start() {
      if (this.submitting) return
      if (!hasPerm('detect.create')) {
        uni.showToast({ title: '没有检测权限', icon: 'none' })
        return
      }
      if (!this.files.length) return
      this.submitting = true
      this.finished = 0
      const paths = []
      for (let i = 0; i < this.files.length; i++) {
        paths.push(await compressImage(this.files[i]))
      }
      this.items = paths.map(() => ({ status: 'waiting', progress: 0, error: '' }))
      try {
        const batch = await request({ url: '/api/detections/batches/', method: 'POST', data: { total: paths.length } })
        for (let i = 0; i < paths.length; i++) {
          this.items[i].status = 'uploading'
          const record = await upload({
            url: '/api/detections/batches/' + batch.id + '/images/',
            filePath: paths[i],
            onProgress: (progress) => { this.items[i].progress = progress }
          })
          this.items[i].status = record.status
          this.items[i].error = record.error_message || ''
          if (record.status === 'success' || record.status === 'failed') this.finished += 1
        }
        let current = await request({ url: '/api/detections/batches/' + batch.id + '/start/', method: 'POST', data: {} })
        this.applyBatch(current)
        if (current.status !== 'finished') current = await this.poll(batch.id)
        this.applyBatch(current)
        uni.navigateTo({ url: '/pages/result/result?batchId=' + batch.id })
      } catch (error) {
        /* 请求层已提示 */
      } finally {
        this.submitting = false
      }
    },
    applyBatch(batch) {
      this.finished = batch.finished || 0
      const records = batch.records || []
      records.forEach((record, index) => {
        if (!this.items[index]) return
        if (record.status && record.status !== 'pending') {
          this.items[index].status = record.status
          this.items[index].error = record.error_message || ''
        }
      })
    },
    poll(id) {
      return new Promise((resolve, reject) => {
        let marker = ''
        let changedAt = Date.now()
        const timer = setInterval(async () => {
          try {
            const data = await request({ url: '/api/detections/batches/' + id + '/', silent: true })
            const next = data.status + ':' + data.finished
            if (next !== marker) {
              marker = next
              changedAt = Date.now()
            }
            this.applyBatch(data)
            if (data.status === 'finished') {
              clearInterval(timer)
              resolve(data)
            } else if (Date.now() - changedAt > 20000) {
              clearInterval(timer)
              uni.showToast({ title: '检测超时，请重试', icon: 'none' })
              reject(new Error('timeout'))
            }
          } catch (error) {
            clearInterval(timer)
            reject(error)
          }
        }, 1000)
      })
    }
  }
}
</script>

<style scoped>
.title { display: block; font-size: 34rpx; font-weight: 700; margin-bottom: 12rpx; }
.pick { margin-top: 24rpx; }
.grid { display: flex; flex-wrap: wrap; margin-top: 20rpx; }
.shot { width: 200rpx; height: 200rpx; border-radius: 16rpx; margin: 0 16rpx 16rpx 0; background: #e2e8f0; }
.line { display: flex; justify-content: space-between; padding: 16rpx 0; border-bottom: 1rpx solid #f1f5f9; }
.state { color: #0e7490; }
</style>
