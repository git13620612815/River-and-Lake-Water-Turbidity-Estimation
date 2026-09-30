<template>
  <el-card shadow="never">
    <div class="toolbar">
      <el-select v-model="query.user_id" clearable filterable placeholder="全部用户" style="width: 180px">
        <el-option v-for="item in users" :key="item.id" :label="item.nickname" :value="String(item.id)" />
      </el-select>
      <el-select v-model="query.label" clearable placeholder="全部等级" style="width: 140px">
        <el-option v-for="item in LEVELS" :key="item.code" :label="item.name" :value="item.code" />
      </el-select>
      <el-date-picker v-model="query.start" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" />
      <el-date-picker v-model="query.end" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" />
      <el-button type="primary" @click="load(1)">查询</el-button>
    </div>
    <el-table :data="rows" border>
      <el-table-column label="图片" width="110">
        <template #default="{ row }"><el-image v-if="row.image" :src="mediaUrl(row.image)" style="width: 72px; height: 54px" fit="cover" /></template>
      </el-table-column>
      <el-table-column label="用户"><template #default="{ row }">{{ row.user && row.user.nickname }}</template></el-table-column>
      <el-table-column label="等级"><template #default="{ row }">{{ row.label_name || '未完成' }}</template></el-table-column>
      <el-table-column label="置信度"><template #default="{ row }">{{ percent(row.confidence) }}</template></el-table-column>
      <el-table-column label="NTU"><template #default="{ row }">{{ row.ntu ?? '-' }}</template></el-table-column>
      <el-table-column prop="status" label="状态" />
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column label="操作" width="90">
        <template #default="{ row }"><el-button link type="primary" @click="open(row)">详情</el-button></template>
      </el-table-column>
    </el-table>
    <el-pagination class="pager" layout="prev, pager, next" :total="total" :page-size="10" @current-change="load" />
    <el-drawer v-model="visible" title="检测详情" size="480px" @opened="draw">
      <template v-if="current">
        <el-image v-if="current.image" :src="mediaUrl(current.image)" style="width: 100%; height: 220px" fit="contain" />
        <p v-if="current.status === 'success'">{{ current.label_name }} · {{ current.ntu }} NTU · 置信度 {{ percent(current.confidence) }}</p>
        <p v-else>{{ current.error_message || '未完成' }}</p>
        <p>{{ current.description }}</p>
        <p v-if="current.note">{{ current.note }}</p>
        <p>参考区间 {{ current.ntu_min }}～{{ current.ntu_max }} NTU</p>
        <div ref="chartRef" class="chart"></div>
      </template>
    </el-drawer>
  </el-card>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import http, { LEVELS, mediaUrl } from '../../api/http'

const route = useRoute()
const users = ref([])
const rows = ref([])
const total = ref(0)
const visible = ref(false)
const current = ref(null)
const chartRef = ref(null)
let chart = null
const query = reactive({ user_id: route.query.user_id ? String(route.query.user_id) : '', label: '', start: '', end: '' })

function percent(value) {
  if (value === null || value === undefined || value === '') return '-'
  return `${(Number(value) * 100).toFixed(2)}%`
}

async function load(page = 1) {
  const data = await http.get('/api/detections/records/', { params: { ...query, page, page_size: 10 } })
  rows.value = data.results
  total.value = data.count
}

async function open(row) {
  current.value = await http.get(`/api/detections/records/${row.id}/`)
  visible.value = true
}

async function draw() {
  await nextTick()
  if (!chartRef.value || !current.value || !current.value.probabilities) return
  if (!chart) chart = echarts.init(chartRef.value)
  const probs = current.value.probabilities
  chart.setOption({
    title: { text: '置信度分布', left: 'center', textStyle: { fontSize: 14 } },
    grid: { left: 90, right: 24, top: 40, bottom: 24 },
    xAxis: { type: 'value', max: 100 },
    yAxis: { type: 'category', data: LEVELS.map((item) => item.name) },
    series: [{
      type: 'bar',
      data: LEVELS.map((item) => ({
        value: Math.round((Number(probs[item.code]) || 0) * 10000) / 100,
        itemStyle: { color: item.color }
      }))
    }]
  })
}

onMounted(async () => {
  try {
    const data = await http.get('/api/admin/users/', { params: { page_size: 50 } })
    users.value = data.results
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  }
})
</script>

<style scoped>
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.pager { margin-top: 12px; justify-content: flex-end; }
.chart { height: 280px; }
</style>
