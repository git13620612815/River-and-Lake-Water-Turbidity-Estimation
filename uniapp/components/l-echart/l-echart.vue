<template>
  <view class="chart">
    <view v-if="!bars.length" class="empty">暂无置信度分布</view>
    <view v-for="item in bars" :key="item.code" class="row" @click="active = item">
      <text class="name">{{ item.name }}</text>
      <view class="track">
        <view class="bar" :style="{ width: item.value + '%', background: item.color }"></view>
      </view>
      <text class="val">{{ item.value.toFixed(2) }}%</text>
    </view>
    <view v-if="active" class="tip">{{ active.name }}　置信度 {{ active.value.toFixed(2) }}%</view>
  </view>
</template>

<script>
export default {
  data() {
    return { bars: [], active: null }
  },
  methods: {
    init(echarts, callback) {
      const chart = { setOption: (option) => this.setOption(option) }
      if (callback) callback(chart)
      return chart
    },
    setOption(option) {
      const series = option && option.series && option.series[0] ? option.series[0].data : []
      this.bars = series || []
      this.active = this.bars[0] || null
    }
  }
}
</script>

<style scoped>
.chart { padding: 8rpx 0 12rpx; }
.empty { color: #94a3b8; font-size: 26rpx; }
.row { display: flex; align-items: center; margin-top: 18rpx; }
.name { width: 140rpx; font-size: 24rpx; color: #334155; }
.track { flex: 1; height: 22rpx; background: #e2e8f0; border-radius: 999rpx; overflow: hidden; }
.bar { height: 100%; border-radius: 999rpx; }
.val { width: 120rpx; text-align: right; font-size: 22rpx; color: #475569; }
.tip { margin-top: 16rpx; font-size: 24rpx; color: #0e7490; }
</style>
