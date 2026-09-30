<template>
  <div>
    <el-card shadow="never" class="block">
      <div class="stats">
        <span v-for="item in LEVELS" :key="item.code" :class="{ low: countOf(item.code) < minRecommended }">
          {{ item.name }} {{ countOf(item.code) }} 张
        </span>
      </div>
      <p v-if="short" class="warn">有类别少于 {{ minRecommended }} 张，训练前请继续补充。样本不足的类别在概览图中为红色。</p>
      <p class="hint">导出和训练在服务器执行：python manage.py export_dataset ，然后 python ml/train.py 。不要在网页里启动训练。</p>
    </el-card>
    <el-card shadow="never" class="block">
      <el-form inline>
        <el-form-item label="等级">
          <el-select v-model="upload.label" style="width: 140px">
            <el-option v-for="item in LEVELS" :key="item.code" :label="item.name" :value="item.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="upload.note" /></el-form-item>
        <el-upload :auto-upload="false" multiple :show-file-list="true" :on-change="onPick" :file-list="fileList">
          <el-button>选择图片</el-button>
        </el-upload>
        <el-button type="primary" :loading="uploading" @click="submitUpload">上传</el-button>
      </el-form>
    </el-card>
    <el-card shadow="never">
      <el-select v-model="filter" clearable placeholder="全部等级" style="width: 160px; margin-bottom: 12px" @change="load(1)">
        <el-option v-for="item in LEVELS" :key="item.code" :label="item.name" :value="item.code" />
      </el-select>
      <el-table :data="rows" border>
        <el-table-column label="图片" width="120">
          <template #default="{ row }"><el-image :src="mediaUrl(row.image)" style="width: 88px; height: 64px" fit="cover" :preview-src-list="[mediaUrl(row.image)]" /></template>
        </el-table-column>
        <el-table-column prop="label_name" label="等级" />
        <el-table-column label="尺寸"><template #default="{ row }">{{ row.width }}×{{ row.height }}</template></el-table-column>
        <el-table-column prop="note" label="备注" />
        <el-table-column prop="uploader_name" label="上传人" />
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button link @click="openLabel(row)">改等级</el-button>
            <el-button link @click="openReplace(row)">替换</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination class="pager" layout="prev, pager, next" :total="total" :page-size="10" @current-change="load" />
    </el-card>
    <el-dialog v-model="labelVisible" title="修改等级" width="360px">
      <el-select v-model="labelForm.label" style="width: 100%">
        <el-option v-for="item in LEVELS" :key="item.code" :label="item.name" :value="item.code" />
      </el-select>
      <template #footer><el-button type="primary" @click="saveLabel">保存</el-button></template>
    </el-dialog>
    <el-dialog v-model="replaceVisible" title="替换图片" width="420px">
      <input type="file" accept="image/*" @change="onReplaceFile" />
      <template #footer><el-button type="primary" @click="saveReplace">上传替换</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http, { LEVELS, mediaUrl } from '../../api/http'

const stats = ref({})
const minRecommended = ref(50)
const rows = ref([])
const total = ref(0)
const filter = ref('')
const fileList = ref([])
const uploading = ref(false)
const upload = reactive({ label: 'clear', note: '' })
const labelVisible = ref(false)
const replaceVisible = ref(false)
const labelForm = reactive({ id: null, label: 'clear' })
const replaceForm = reactive({ id: null, file: null })
const short = computed(() => LEVELS.some((item) => countOf(item.code) < minRecommended.value))

function countOf(code) {
  return Number(stats.value[code] || 0)
}

async function loadStats() {
  stats.value = await http.get('/api/admin/datasets/stats/')
  minRecommended.value = stats.value.min_recommended || 50
}

async function load(page = 1) {
  const data = await http.get('/api/admin/datasets/', { params: { label: filter.value, page, page_size: 10 } })
  rows.value = data.results
  total.value = data.count
}

function onPick(file, files) {
  fileList.value = files
}

async function submitUpload() {
  const raws = fileList.value.map((item) => item.raw).filter(Boolean)
  if (!raws.length) return
  uploading.value = true
  try {
    for (let index = 0; index < raws.length; index += 20) {
      const form = new FormData()
      form.append('label', upload.label)
      form.append('note', upload.note)
      raws.slice(index, index + 20).forEach((file) => form.append('files', file))
      await http.post('/api/admin/datasets/', form)
    }
    fileList.value = []
    upload.note = ''
    ElMessage.success('上传完成')
    await loadStats()
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    uploading.value = false
  }
}

function openLabel(row) {
  labelForm.id = row.id
  labelForm.label = row.label
  labelVisible.value = true
}

async function saveLabel() {
  try {
    await http.patch(`/api/admin/datasets/${labelForm.id}/`, { label: labelForm.label })
    labelVisible.value = false
    await loadStats()
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

function openReplace(row) {
  replaceForm.id = row.id
  replaceForm.file = null
  replaceVisible.value = true
}

function onReplaceFile(event) {
  replaceForm.file = event.target.files[0]
}

async function saveReplace() {
  if (!replaceForm.file) return
  const form = new FormData()
  form.append('file', replaceForm.file)
  try {
    await http.post(`/api/admin/datasets/${replaceForm.id}/replace/`, form)
    replaceVisible.value = false
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm('删除数据集图片不会影响已有检测记录', '删除样本')
    await http.delete(`/api/admin/datasets/${row.id}/`)
    await loadStats()
    await load()
  } catch (error) {
    if (error !== 'cancel' && error.message) ElMessage.error(error.message)
  }
}

onMounted(async () => {
  try {
    await loadStats()
    await load()
  } catch (error) {
    ElMessage.error(error.message)
  }
})
</script>

<style scoped>
.block { margin-bottom: 16px; }
.stats { display: flex; gap: 16px; flex-wrap: wrap; }
.low { color: #dc2626; }
.warn, .hint { color: #9a3412; }
.hint { color: #64748b; }
.pager { margin-top: 12px; justify-content: flex-end; }
</style>
