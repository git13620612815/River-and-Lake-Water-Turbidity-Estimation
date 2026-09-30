<template>
  <view class="page" v-if="current">
    <swiper class="swiper" :current="index" @change="onChange">
      <swiper-item v-for="item in records" :key="item.id">
        <image v-if="item.image" class="photo" :src="mediaUrl(item.image)" mode="aspectFit" @click="preview(item)" />
        <view v-else class="photo empty">无预览</view>
      </swiper-item>
    </swiper>
    <text class="indicator">{{ index + 1 }}/{{ records.length }}</text>
    <view class="card" v-if="current.status === 'success'">
      <text class="level" :style="{ color: meta.color }">{{ current.label_name }}</text>
      <text class="ntu">{{ ntuText(current.ntu) }} NTU</text>
      <text class="muted">置信度 {{ percent(current.confidence) }} · 参考区间 {{ current.ntu_min }}～{{ current.ntu_max }} NTU</text>
      <text class="desc">{{ current.description }}</text>
      <text class="warn" v-if="current.low_confidence">置信度偏低，建议重拍或换角度</text>
      <text class="note" v-if="current.note">{{ current.note }}</text>
      <text class="range-note">区间为等级参考范围，点估值为概率加权结果。</text>
      <text class="chart-title">置信度分布</text>
      <l-echart ref="chartRef" />
    </view>
    <view class="card" v-else>
      <text class="level fail">这张图片未完成检测</text>
      <text class="muted">{{ current.error_message || '请重新拍摄' }}</text>
    </view>
    <view class="actions">
      <button class="ghost-btn" @click="goHistory">查看历史</button>
      <button class="primary-btn" @click="again">重新检测</button>
    </view>
  </view>
</template>

<script>
import LEchart from '../../components/l-echart/l-echart.vue'
import { request } from '../../utils/request.js'
import { mediaUrl, percent, ntuText, labelMeta, buildOption } from '../../utils/config.js'

export default {
  components: { LEchart },
  data() {
    return { batchId: '', records: [], index: 0, chart: null }
  },
  computed: {
    current() {
      return this.records[this.index] || null
    },
    meta() {
      return labelMeta(this.current && this.current.label)
    }
  },
  onLoad(query) {
    this.batchId = query.batchId
    this.load()
  },
  methods: {
    mediaUrl, percent, ntuText,
    load() {
      request({ url: '/api/detections/batches/' + this.batchId + '/' }).then((data) => {
        this.records = data.records || []
        const successIndex = this.records.findIndex((item) => item.status === 'success')
        this.index = successIndex >= 0 ? successIndex : 0
        this.$nextTick(() => this.draw())
      })
    },
    onChange(event) {
      this.index = event.detail.current
      this.draw()
    },
    draw() {
      const current = this.current
      if (!current || current.status !== 'success' || !current.probabilities) {
        this.chart = null
        return
      }
      const option = buildOption(current.probabilities)
      this.$nextTick(() => {
        const ref = this.$refs.chartRef
        if (!ref) return
        if (!this.chart) {
          this.chart = ref.init(null, (chart) => chart.setOption(option))
        } else {
          this.chart.setOption(option)
        }
      })
    },
    preview(item) {
      const urls = this.records.filter((row) => row.image).map((row) => mediaUrl(row.image))
      uni.previewImage({ current: mediaUrl(item.image), urls })
    },
    goHistory() {
      uni.switchTab({ url: '/pages/history/history' })
    },
    again() {
      uni.switchTab({ url: '/pages/detect/detect' })
    }
  }
}
</script>

<style scoped>
.swiper { height: 460rpx; background: #082f49; }
.photo { width: 100%; height: 460rpx; }
.empty { color: #fff; display: flex; align-items: center; justify-content: center; }
.indicator { display: block; text-align: center; margin-top: 12rpx; color: #64748b; }
.level { display: block; font-size: 44rpx; font-weight: 700; }
.fail { color: #dc2626; font-size: 34rpx; }
.ntu { display: block; margin: 8rpx 0; font-size: 36rpx; }
.desc, .note, .range-note, .warn { display: block; margin-top: 12rpx; line-height: 1.6; }
.warn { color: #b45309; }
.note { color: #9a3412; }
.chart-title { display: block; margin-top: 28rpx; font-weight: 700; }
.actions { display: flex; gap: 20rpx; padding: 0 24rpx 40rpx; }
.actions button { flex: 1; }
</style>
