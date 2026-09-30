<template>
  <view>
    <view class="filters card">
      <picker :range="labelNames" :value="labelIndex" @change="onLabel">
        <view class="filter">{{ labelNames[labelIndex] }}</view>
      </picker>
      <picker mode="date" :value="start" @change="onStart">
        <view class="filter">{{ start || '开始日期' }}</view>
      </picker>
      <picker mode="date" :value="end" @change="onEnd">
        <view class="filter">{{ end || '结束日期' }}</view>
      </picker>
    </view>
    <view class="toolbar" v-if="list.length">
      <text @click="managing = !managing">{{ managing ? '完成' : '管理' }}</text>
      <text v-if="managing" class="danger" @click="removeSelected">删除所选</text>
    </view>
    <view v-if="!list.length" class="card empty">还没有检测记录，去拍摄一张水面照片</view>
    <view v-for="item in list" :key="item.id" class="card row" @click="open(item)">
      <checkbox v-if="managing" :checked="selected.indexOf(item.id) >= 0" @click.stop="toggle(item.id)" />
      <image v-if="item.image" class="thumb" :src="mediaUrl(item.image)" mode="aspectFill" />
      <view class="info">
        <text class="name" :style="{ color: colorOf(item) }">{{ item.label_name || '未完成' }}</text>
        <text class="muted" v-if="item.status === 'success'">{{ ntuText(item.ntu) }} NTU · {{ percent(item.confidence) }}</text>
        <text class="muted" v-else>{{ item.error_message }}</text>
        <text class="time">{{ item.created_at }}</text>
      </view>
      <text v-if="!managing" class="del" @click.stop="removeOne(item)">删除</text>
    </view>
  </view>
</template>

<script>
import { ensureLogin, request } from '../../utils/request.js'
import { LABELS, mediaUrl, percent, ntuText, labelMeta } from '../../utils/config.js'

export default {
  data() {
    return {
      labelNames: ['全部等级'].concat(LABELS.map((item) => item.name)),
      labelIndex: 0,
      start: '',
      end: '',
      page: 1,
      list: [],
      finished: false,
      managing: false,
      selected: []
    }
  },
  onShow() {
    if (!ensureLogin()) return
    this.reload()
  },
  onPullDownRefresh() {
    this.reload().finally(() => uni.stopPullDownRefresh())
  },
  onReachBottom() {
    if (!this.finished) this.load()
  },
  methods: {
    mediaUrl, percent, ntuText,
    colorOf(item) {
      return labelMeta(item.label).color
    },
    reload() {
      this.page = 1
      this.list = []
      this.finished = false
      this.selected = []
      return this.load()
    },
    load() {
      const label = this.labelIndex === 0 ? '' : LABELS[this.labelIndex - 1].code
      return request({
        url: '/api/detections/records/',
        data: { page: this.page, page_size: 10, label, start: this.start, end: this.end }
      }).then((data) => {
        const rows = data.results || []
        this.list = this.list.concat(rows)
        if (this.list.length >= data.count || !rows.length) this.finished = true
        else this.page += 1
      })
    },
    onLabel(event) {
      this.labelIndex = Number(event.detail.value)
      this.reload()
    },
    onStart(event) {
      this.start = event.detail.value
      this.reload()
    },
    onEnd(event) {
      this.end = event.detail.value
      this.reload()
    },
    open(item) {
      if (this.managing) {
        this.toggle(item.id)
        return
      }
      uni.navigateTo({ url: '/pages/history/detail?id=' + item.id })
    },
    toggle(id) {
      const index = this.selected.indexOf(id)
      if (index >= 0) this.selected.splice(index, 1)
      else this.selected.push(id)
    },
    removeOne(item) {
      uni.showModal({
        title: '删除记录',
        content: '删除后不可恢复',
        success: (res) => {
          if (!res.confirm) return
          request({ url: '/api/detections/records/' + item.id + '/', method: 'DELETE' }).then(() => this.reload())
        }
      })
    },
    removeSelected() {
      if (!this.selected.length) return
      uni.showModal({
        title: '删除记录',
        content: '确定删除选中的 ' + this.selected.length + ' 条记录？',
        success: (res) => {
          if (!res.confirm) return
          request({ url: '/api/detections/records/bulk-delete/', method: 'POST', data: { ids: this.selected } }).then(() => {
            this.managing = false
            this.reload()
          })
        }
      })
    }
  }
}
</script>

<style scoped>
.filters { display: flex; justify-content: space-between; }
.filter { background: #f1f5f9; border-radius: 12rpx; padding: 12rpx 16rpx; font-size: 24rpx; }
.toolbar { display: flex; justify-content: space-between; padding: 0 32rpx; color: #0e7490; }
.danger { color: #dc2626; }
.row { display: flex; align-items: center; }
.thumb { width: 120rpx; height: 120rpx; border-radius: 12rpx; margin: 0 16rpx; background: #e2e8f0; }
.info { flex: 1; }
.name { display: block; font-weight: 700; }
.time { display: block; color: #94a3b8; font-size: 22rpx; margin-top: 6rpx; }
.del { color: #dc2626; font-size: 24rpx; }
.empty { color: #64748b; }
</style>
