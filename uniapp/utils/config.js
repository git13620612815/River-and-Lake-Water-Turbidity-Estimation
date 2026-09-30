export const baseURL = 'http://127.0.0.1:8000'

export const LABELS = [
  { code: 'clear', name: '清澈', color: '#0284c7' },
  { code: 'slight', name: '轻度浑浊', color: '#0d9488' },
  { code: 'moderate', name: '中度浑浊', color: '#ea580c' },
  { code: 'severe', name: '重度浑浊', color: '#dc2626' }
]

export function labelMeta(code) {
  return LABELS.find((item) => item.code === code) || { code, name: '未知', color: '#64748b' }
}

export function mediaUrl(path) {
  if (!path) return ''
  if (path.indexOf('http') === 0) return path
  return baseURL + path
}

export function percent(value) {
  if (value === null || value === undefined || value === '') return '--'
  return (Number(value) * 100).toFixed(2) + '%'
}

export function ntuText(value) {
  if (value === null || value === undefined || value === '') return '--'
  return Number(value).toFixed(1)
}

export function normalizeProbs(probabilities) {
  const probs = probabilities || {}
  const sum = LABELS.reduce((total, item) => total + (Number(probs[item.code]) || 0), 0) || 1
  const result = {}
  LABELS.forEach((item) => {
    result[item.code] = (Number(probs[item.code]) || 0) / sum
  })
  return result
}

export function buildOption(probabilities) {
  const probs = normalizeProbs(probabilities)
  return {
    yAxis: { data: LABELS.map((item) => item.name) },
    series: [{
      data: LABELS.map((item) => ({
        name: item.name,
        code: item.code,
        value: Math.round(probs[item.code] * 10000) / 100,
        color: item.color
      }))
    }]
  }
}
