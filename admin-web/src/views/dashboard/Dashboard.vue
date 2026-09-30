<template>
  <div>
    <el-row :gutter="16">
      <el-col :span="6" v-for="item in cards" :key="item.label">
        <el-card shadow="never"><div class="num">{{ item.value }}</div><div class="label">{{ item.label }}</div></el-card>
      </el-col>
    </el-row>
    <el-row :gutter="16" class="charts">
      <el-col :span="12"><el-card shadow="never"><div ref="levelRef" class="chart"></div></el-card></el-col>
      <el-col :span="12"><el-card shadow="never"><div ref="dailyRef" class="chart"></div></el-card></el-col>
    </el-row>
    <el-card shadow="never"><div ref="dataRef" class="chart"></div></el-card>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import http, { LEVELS } from '../../api/http'

const stats = ref(null)
const levelRef = ref(null)
const dailyRef = ref(null)
const dataRef = ref(null)
const charts = []

const cards = computed(() => {
  const data = stats.value || {}
  return [
    { label: '用户总数', value: data.user_count ?? '-' },
    { label: '今日检测', value: data.today_detection_count ?? '-' },
    { label: '数据集张数', value: data.dataset_count ?? '-' },
    { label: '模型状态', value: data.model_ready ? 'YOLOv8 已就绪' : '图像特征模型' }
  ]
})

function mountChart(el, option) {
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
}

function render() {
  const data = stats.value
  const names = LEVELS.map((item) => item.name)
  mountChart(levelRef.value, {
    title: { text: '浊度等级检测次数', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {},
    xAxis: { type: 'category', data: names },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'bar', data: LEVELS.map((item) => data.level_counts[item.code] || 0), itemStyle: { color: '#0e7490' } }]
  })
  mountChart(dailyRef.value, {
    title: { text: '最近 7 天检测量', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {},
    xAxis: { type: 'category', data: data.daily_counts.map((item) => item.date.slice(5)) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ type: 'line', data: data.daily_counts.map((item) => item.count), smooth: true, itemStyle: { color: '#0284c7' } }]
  })
  const minCount = data.min_recommended || 50
  mountChart(dataRef.value, {
    title: { text: '数据集各类数量', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {},
    xAxis: { type: 'category', data: names },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'bar',
      data: LEVELS.map((item) => {
        const value = data.dataset_counts[item.code] || 0
        return { value, itemStyle: { color: value < minCount ? '#dc2626' : '#0d9488' } }
      })
    }]
  })
}

function onResize() {
  charts.forEach((chart) => chart.resize())
}

onMounted(async () => {
  try {
    stats.value = await http.get('/api/admin/dashboard/')
    await nextTick()
    render()
    window.addEventListener('resize', onResize)
  } catch (error) {
    ElMessage.error(error.message)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  charts.forEach((chart) => chart.dispose())
})
</script>

<style scoped>
.num { font-size: 28px; font-weight: 700; color: #0e7490; }
.label { color: #64748b; margin-top: 6px; }
.charts { margin: 16px 0; }
.chart { height: 320px; }
</style>
