<template>
  <view v-if="record">
    <image v-if="record.image" class="photo" :src="mediaUrl(record.image)" mode="aspectFit" @click="preview" />
    <view class="card" v-if="record.status === 'success'">
      <text class="level" :style="{ color: meta.color }">{{ record.label_name }}</text>
      <text class="ntu">{{ ntuText(record.ntu) }} NTU</text>
      <text class="muted">置信度 {{ percent(record.confidence) }} · 参考区间 {{ record.ntu_min }}～{{ record.ntu_max }} NTU</text>
      <text class="desc">{{ record.description }}</text>
      <text class="warn" v-if="record.low_confidence">置信度偏低，建议重拍或换角度</text>
      <text class="note" v-if="record.note">{{ record.note }}</text>
      <text class="time">{{ record.created_at }}</text>
      <text class="chart-title">置信度分布</text>
      <l-echart ref="chartRef" />
    </view>
    <view class="card" v-else>
      <text class="level fail">检测未完成</text>
      <text class="muted">{{ record.error_message }}</text>
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
    return { record: null }
  },
  computed: {
    meta() {
      return labelMeta(this.record && this.record.label)
    }
  },
  onLoad(query) {
    request({ url: '/api/detections/records/' + query.id + '/' }).then((record) => {
      this.record = record
      this.$nextTick(() => {
        if (!record.probabilities || !this.$refs.chartRef) return
        this.$refs.chartRef.init(null, (chart) => chart.setOption(buildOption(record.probabilities)))
      })
    })
  },
  methods: {
    mediaUrl, percent, ntuText,
    preview() {
      uni.previewImage({ urls: [mediaUrl(this.record.image)] })
    }
  }
}
</script>

<style scoped>
.photo { width: 100%; height: 460rpx; background: #082f49; }
.level { display: block; font-size: 44rpx; font-weight: 700; }
.fail { color: #dc2626; font-size: 34rpx; }
.ntu { display: block; margin: 8rpx 0; font-size: 36rpx; }
.desc, .note, .warn, .time { display: block; margin-top: 12rpx; line-height: 1.6; }
.warn { color: #b45309; }
.note { color: #9a3412; }
.time { color: #94a3b8; }
.chart-title { display: block; margin-top: 28rpx; font-weight: 700; }
</style>
