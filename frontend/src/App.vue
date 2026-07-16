<template>
  <div class="app-container">
    <!-- 顶部科技感 Header -->
    <header class="app-header">
      <div class="logo-box">
        <el-icon class="logo-icon"><DataAnalysis /></el-icon>
        <h1 class="gradient-text">电商评论智能洞察系统 <span class="version-tag">Pro v2.0</span></h1>
      </div>
      <p class="subtitle">Powered by BERT & ECharts Large-scale Data Visualization</p>
    </header>
    
    <div class="main-content">
      <el-tabs v-model="activeTab" class="modern-tabs" @tab-click="handleTabClick">
        
        <!-- ================= 模块 1：数据看板 (第二阶段大屏) ================= -->
        <el-tab-pane label="📊 深度数据洞察大屏" name="dashboard">
          
          <!-- 顶层：AI 智能总结卡片 -->
          <el-card v-if="summaryData" class="glass-card ai-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <strong class="ai-title"><el-icon><Cpu /></el-icon> AI 智能评论总结</strong>
                <el-tag effect="dark" :type="summaryData.mode === 'rule_fallback' ? 'warning' : 'success'" round>
                  {{ summaryData.mode === 'rule_fallback' ? '规则引擎分析中' : '大模型深度解析' }}
                </el-tag>
              </div>
            </template>
            <el-row :gutter="30">
              <el-col :span="8">
                <div class="insight-box positive-box">
                  <h4><el-icon><Trophy /></el-icon> 核心优点</h4>
                  <ul>
                    <li v-for="(item, idx) in summaryData.advantages" :key="idx">{{ item }}</li>
                  </ul>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="insight-box negative-box">
                  <h4><el-icon><Warning /></el-icon> 主要槽点</h4>
                  <ul>
                    <li v-for="(item, idx) in summaryData.disadvantages" :key="idx">{{ item }}</li>
                  </ul>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="insight-box advice-box">
                  <!-- 把 <Lightbulb /> 改成 <Star /> -->
                  <h4><el-icon><Star /></el-icon> 购买建议</h4>
                  <p>{{ summaryData.buying_advice }}</p>
                </div>
              </el-col>
            </el-row>
          </el-card>

          <!-- 中层：三大基础图表 -->
          <el-row :gutter="20" class="chart-row">
            <el-col :span="8">
              <el-card class="glass-card" shadow="hover">
                <template #header><strong class="chart-title">总体情感分布</strong></template>
                <div id="pieChart" class="chart-container"></div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="glass-card" shadow="hover">
                <template #header><strong class="chart-title">情感强度波动趋势</strong></template>
                <div id="barChart" class="chart-container"></div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="glass-card" shadow="hover">
                <template #header><strong class="chart-title">多维评价雷达分析</strong></template>
                <div id="radarChart" class="chart-container"></div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 底层：双色词云 -->
          <el-row :gutter="20" class="chart-row">
            <el-col :span="12">
              <el-card class="glass-card" shadow="hover">
                <template #header><strong class="chart-title text-green">✨ 用户点赞高频词云</strong></template>
                <div id="posWordCloud" class="chart-container"></div>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="glass-card" shadow="hover">
                <template #header><strong class="chart-title text-red">🔥 用户吐槽高频词云</strong></template>
                <div id="negWordCloud" class="chart-container"></div>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>

        <!-- ================= 模块 2：单条分析 ================= -->
        <el-tab-pane label="🤖 实时推理沙箱" name="single">
          <div class="sandbox-container">
            <el-card class="glass-card input-card" shadow="never">
              <h3 style="margin-top:0;">输入单条文本进行情感预测</h3>
              <el-input v-model="inputText" type="textarea" :rows="5" resize="none" placeholder="输入你想测试的商品评论，感受 BERT 模型的威力..." />
              <div style="margin-top: 20px; text-align: right;">
                <el-button type="primary" size="large" round :loading="loadingSingle" @click="handleAnalyzeSingle">
                  <el-icon style="margin-right:5px;"><VideoPlay /></el-icon> 启动推理引擎
                </el-button>
              </div>
            </el-card>

            <transition name="fade-slide">
              <el-card v-if="resultSingle" class="glass-card result-card" shadow="always" style="margin-top: 20px;">
                <template #header><strong style="font-size: 18px;">推理结果</strong></template>
                <div class="result-grid">
                  <div class="result-item">
                    <span class="label">情感极性</span>
                    <el-tag :type="resultSingle.sentiment === 'positive' ? 'success' : 'danger'" effect="dark" size="large" round>
                      {{ resultSingle.sentiment === 'positive' ? '😊 正向 Positive' : '😡 负向 Negative' }}
                    </el-tag>
                  </div>
                  <div class="result-item">
                    <span class="label">AI 置信度 (Confidence)</span>
                    <span class="value number">{{ (resultSingle.confidence * 100).toFixed(2) }}%</span>
                  </div>
                  <div class="result-item">
                    <span class="label">情绪强度 (Intensity)</span>
                    <span class="value number">{{ resultSingle.strength }}<span style="font-size:14px;color:#999;">/10</span></span>
                  </div>
                </div>
              </el-card>
            </transition>
          </div>
        </el-tab-pane>

        <!-- ================= 模块 3：历史记录 ================= -->
        <el-tab-pane label="📚 知识库与检索" name="history">
          <el-card class="glass-card" shadow="never">
            <div class="filter-bar">
              <el-select v-model="filterSentiment" placeholder="所有情感类别" clearable class="filter-item">
                <el-option label="😊 正向评论" value="positive" />
                <el-option label="😡 负向评论" value="negative" />
              </el-select>
              <el-date-picker v-model="filterTime" type="daterange" range-separator="→" start-placeholder="开始日期" end-placeholder="结束日期" value-format="YYYY-MM-DD" class="filter-item" />
              <el-button type="primary" round @click="handleSearch">
                <el-icon style="margin-right:5px;"><Search /></el-icon>深度检索
              </el-button>
            </div>

            <el-table :data="historyData" style="width: 100%; border-radius: 8px; overflow: hidden;" :header-cell-style="{ background: '#f5f7fa', color: '#333', fontWeight: 'bold' }">
              <el-table-column prop="id" label="标识 ID" width="100" align="center" />
              <el-table-column prop="raw_text" label="原始数据 (Raw Text)" show-overflow-tooltip />
              <el-table-column prop="sentiment" label="分析极性" width="120" align="center">
                <template #default="scope">
                  <el-tag :type="scope.row.sentiment === 'positive' ? 'success' : 'danger'" effect="light">
                    {{ scope.row.sentiment === 'positive' ? '正向' : '负向' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="strength" label="强度分数" width="100" align="center" />
              <el-table-column label="详细记录" width="120" align="center">
                <template #default="scope">
                  <el-button size="small" type="primary" plain round @click="showDetail(scope.row)">溯源</el-button>
                </template>
              </el-table-column>
            </el-table>

            <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
              <el-pagination background layout="total, prev, pager, next, jumper" :total="historyTotal" v-model:current-page="historyPage" v-model:page-size="historyPageSize" @current-change="handlePageChange" />
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Cpu, Trophy, Warning, Star, Search, VideoPlay } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import axios from 'axios'

const activeTab = ref('dashboard')
const inputText = ref('')
const loadingSingle = ref(false)
const resultSingle = ref(null)

const statsData = ref({ positive: 0, negative: 0, intensity: [0, 0, 0, 0, 0] })
const summaryData = ref(null)
const radarAspects = ref([])
const posWords = ref([])
const negWords = ref([])

const historyData = ref([])
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyTotal = ref(0)
const filterSentiment = ref('')
const filterTime = ref([])

let pieChart, barChart, radarChart, posWordCloud, negWordCloud

onMounted(async () => {
  await fetchAllDashboardData()
  await fetchHistory()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
})

const safeNumber = (value, fallback = 0) => {
  const numberValue = Number(value)
  return Number.isFinite(numberValue) ? numberValue : fallback
}

const settledData = (result) => {
  if (result.status !== 'fulfilled') return null
  const payload = result.value?.data
  return payload?.success ? payload.data : null
}

const mapWordCloudData = (items = []) => {
  return items
    .filter(item => item?.word && safeNumber(item.count) > 0)
    .map(item => ({ name: item.word, value: safeNumber(item.count) }))
}

const emptySummary = () => ({
  mode: 'rule_fallback',
  advantages: ['当前历史评论较少，暂未形成稳定优点。'],
  disadvantages: ['当前负向证据不足，暂未发现集中槽点。'],
  buying_advice: '请先完成单条或批量评论分析，再查看更完整的商品洞察。'
})

const fetchAllDashboardData = async () => {
  try {
    const [statRes, sumRes, aspectRes, kwRes] = await Promise.allSettled([
      axios.get('/api/statistics/summary'),
      axios.get('/api/summary/product'),
      axios.get('/api/insights/aspects'),
      axios.get('/api/insights/keywords')
    ])

    const statData = settledData(statRes) || {}
    const summary = settledData(sumRes)
    const aspectData = settledData(aspectRes) || {}
    const keywordData = settledData(kwRes) || {}

    statsData.value = {
      positive: safeNumber(statData.positive_count),
      negative: safeNumber(statData.negative_count),
      intensity: Array.isArray(statData.intensity_distribution)
        ? statData.intensity_distribution.map(item => safeNumber(item))
        : [0, 0, 0, 0, 0]
    }
    summaryData.value = summary || emptySummary()
    radarAspects.value = Array.isArray(aspectData.aspects)
      ? aspectData.aspects.map(item => ({ name: item.name, score: safeNumber(item.score) }))
      : [
          { name: '价格', score: 0 },
          { name: '物流', score: 0 },
          { name: '质量', score: 0 }
        ]
    posWords.value = mapWordCloudData(keywordData.positive_words)
    negWords.value = mapWordCloudData(keywordData.negative_words)

    if (!safeNumber(statData.total) && !posWords.value.length && !negWords.value.length) {
      ElMessage.info('暂无历史评论数据，请先完成单条或批量分析')
    }

    if (activeTab.value === 'dashboard') {
      await nextTick()
      initCharts()
    }
  } catch (error) {
    console.error(error)
    summaryData.value = emptySummary()
    ElMessage.error('看板数据加载失败，请检查后端服务')
    if (activeTab.value === 'dashboard') {
      await nextTick()
      initCharts()
    }
  }
}

const disposeCharts = () => {
  ;[pieChart, barChart, radarChart, posWordCloud, negWordCloud].forEach(chart => chart?.dispose())
  pieChart = barChart = radarChart = posWordCloud = negWordCloud = null
}

const wordCloudFallback = (text) => [{ name: text, value: 1, textStyle: { color: '#c0c4cc' } }]

const initCharts = () => {
  disposeCharts()

  if (document.getElementById('pieChart')) {
    pieChart = echarts.init(document.getElementById('pieChart'))
    pieChart.setOption({
      tooltip: { trigger: 'item', backgroundColor: 'rgba(255,255,255,0.9)' },
      legend: { bottom: '5%', icon: 'circle' },
      series: [{
        type: 'pie', radius: ['50%', '75%'], center: ['50%', '45%'],
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        data: [
          { value: statsData.value.positive, name: '正向 (Positive)', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: '#43E97B'}, {offset: 1, color: '#38F9D7'}]) } },
          { value: statsData.value.negative, name: '负向 (Negative)', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: '#FA709A'}, {offset: 1, color: '#FEE140'}]) } }
        ]
      }]
    })
  }

  if (document.getElementById('barChart')) {
    barChart = echarts.init(document.getElementById('barChart'))
    barChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      xAxis: { type: 'category', data: ['极度不满(0-2)', '偏负向(2-4)', '中立(4-6)', '偏正向(6-8)', '极度满意(8-10)'], axisLine: { lineStyle: { color: '#ccc' } } },
      yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: '#eee' } } },
      series: [{
        data: statsData.value.intensity, type: 'bar', barWidth: '40%',
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: '#4FACFE'}, {offset: 1, color: '#00F2FE'}])
        }
      }]
    })
  }

  if (document.getElementById('radarChart')) {
    const radarItems = radarAspects.value.length ? radarAspects.value : [
      { name: '价格', score: 0 },
      { name: '物流', score: 0 },
      { name: '质量', score: 0 }
    ]
    radarChart = echarts.init(document.getElementById('radarChart'))
    radarChart.setOption({
      radar: { indicator: radarItems.map(item => ({ name: item.name, max: 100 })), radius: '60%', splitArea: { show: false }, splitLine: { lineStyle: { color: '#e4e7ed' } } },
      series: [{
        type: 'radar',
        data: [{ value: radarItems.map(item => item.score), name: '口碑评分' }],
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: 'rgba(79, 172, 254, 0.6)'}, {offset: 1, color: 'rgba(0, 242, 254, 0.1)'}]) },
        itemStyle: { color: '#4FACFE', borderColor: '#4FACFE', borderWidth: 2 },
        lineStyle: { width: 3 }
      }]
    })
  }

  if (document.getElementById('posWordCloud')) {
    posWordCloud = echarts.init(document.getElementById('posWordCloud'))
    posWordCloud.setOption({
      series: [{
        type: 'wordCloud', shape: 'circle', gridSize: 8, sizeRange: [16, 60], rotationRange: [0, 0],
        textStyle: { color: () => 'rgb(' + [Math.round(Math.random() * 50), Math.round(Math.random() * 155 + 100), Math.round(Math.random() * 100)].join(',') + ')' },
        data: posWords.value.length ? posWords.value : wordCloudFallback('暂无正向词')
      }]
    })
  }

  if (document.getElementById('negWordCloud')) {
    negWordCloud = echarts.init(document.getElementById('negWordCloud'))
    negWordCloud.setOption({
      series: [{
        type: 'wordCloud', shape: 'circle', gridSize: 8, sizeRange: [16, 60], rotationRange: [0, 0],
        textStyle: { color: () => 'rgb(' + [Math.round(Math.random() * 105 + 150), Math.round(Math.random() * 50), Math.round(Math.random() * 50)].join(',') + ')' },
        data: negWords.value.length ? negWords.value : wordCloudFallback('暂无负向词')
      }]
    })
  }
}

const handleAnalyzeSingle = async () => {
  const text = inputText.value.trim()
  if (!text) {
    ElMessage.warning('请输入评论文本')
    return
  }
  loadingSingle.value = true
  try {
    const response = await axios.post('/api/sentiment/single', {
      text,
      product_id: 'web-single'
    })
    resultSingle.value = response.data.data
    ElMessage.success(`推理完成，情感结果：${resultSingle.value.sentiment}`)
    await fetchAllDashboardData()
    await fetchHistory()
  } catch (error) {
    console.error(error)
    ElMessage.error('单条分析失败，请检查后端服务')
  } finally {
    loadingSingle.value = false
  }
}

const fetchHistory = async () => {
  try {
    const params = {
      page: historyPage.value,
      page_size: historyPageSize.value
    }
    if (filterSentiment.value) params.sentiment = filterSentiment.value
    if (Array.isArray(filterTime.value) && filterTime.value.length === 2) {
      params.start_time = filterTime.value[0]
      params.end_time = filterTime.value[1]
    }
    const response = await axios.get('/api/history', { params })
    const data = response.data.data || {}
    historyData.value = data.items || []
    historyTotal.value = safeNumber(data.total)
  } catch (error) {
    console.error(error)
    ElMessage.error('历史记录加载失败')
  }
}

const handleSearch = async () => {
  historyPage.value = 1
  await fetchHistory()
}

const handlePageChange = async (page) => {
  historyPage.value = page
  await fetchHistory()
}

const showDetail = (row) => {
  ElMessage.info(`记录 ${row.id}：${row.raw_text}`)
}

const handleTabClick = (pane) => {
  if (pane.props.name === 'dashboard') {
    nextTick(() => { initCharts() })
  }
  if (pane.props.name === 'history') {
    fetchHistory()
  }
}

const resizeCharts = () => {
  pieChart?.resize()
  barChart?.resize()
  radarChart?.resize()
  posWordCloud?.resize()
  negWordCloud?.resize()
}

window.addEventListener('resize', resizeCharts)
</script>

<style>
/* ================== 全局重置与高级科技风 UI ================== */
body {
  background-color: #f0f2f5;
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}
.app-container {
  padding: 30px;
  max-width: 1300px;
  margin: 0 auto;
}

/* Header 设计 */
.app-header {
  text-align: center;
  margin-bottom: 40px;
}
.logo-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}
.logo-icon {
  font-size: 36px;
  color: #409EFF;
}
.gradient-text {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #1f2b45, #409EFF);
  -webkit-background-clip: text;
  color: transparent;
  margin: 0;
}
.version-tag {
  font-size: 14px;
  background: #1f2b45;
  color: #fff;
  padding: 4px 10px;
  border-radius: 20px;
  vertical-align: middle;
}
.subtitle {
  color: #909399;
  letter-spacing: 1px;
  margin-top: 10px;
}

/* 导航 Tabs 毛玻璃重构 */
.modern-tabs > .el-tabs__header {
  border-bottom: none;
  background: rgba(255,255,255,0.7);
  backdrop-filter: blur(10px);
  padding: 10px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.modern-tabs > .el-tabs__header .el-tabs__nav {
  border: none !important;
}
.modern-tabs > .el-tabs__header .el-tabs__item {
  border: none !important;
  font-size: 16px;
  font-weight: 600;
  color: #606266;
  border-radius: 8px;
  margin: 0 5px;
  transition: all 0.3s;
}
.modern-tabs > .el-tabs__header .el-tabs__item.is-active {
  background: #409EFF;
  color: #fff;
  box-shadow: 0 4px 12px rgba(64,158,255,0.4);
}

/* 毛玻璃高级卡片 */
.glass-card {
  border: none;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  box-shadow: 0 8px 24px rgba(149, 157, 165, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.glass-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 32px rgba(149, 157, 165, 0.2);
}

/* 智能总结面板 */
.ai-card { border-left: 6px solid #409EFF; margin-bottom: 24px; }
.card-header { display: flex; align-items: center; justify-content: space-between; }
.ai-title { font-size: 18px; color: #1f2b45; display: flex; align-items: center; gap: 8px; }
.insight-box h4 { margin-top: 0; display: flex; align-items: center; gap: 6px; font-size: 16px; }
.positive-box h4 { color: #67C23A; }
.negative-box h4 { color: #F56C6C; }
.advice-box h4 { color: #E6A23C; }
.insight-box ul { padding-left: 20px; color: #606266; line-height: 1.8; }
.insight-box p { color: #606266; line-height: 1.8; padding-left: 5px; }

/* 图表区 */
.chart-row { margin-bottom: 24px; }
.chart-title { font-size: 16px; color: #303133; }
.chart-container { height: 320px; }
.text-green { color: #67C23A !important; }
.text-red { color: #F56C6C !important; }

/* 交互卡片 */
.sandbox-container { max-width: 800px; margin: 0 auto; }
.result-grid { display: flex; justify-content: space-around; padding: 20px 0; }
.result-item { text-align: center; }
.result-item .label { display: block; color: #909399; margin-bottom: 10px; font-size: 14px; }
.result-item .value.number { font-size: 28px; font-weight: bold; color: #1f2b45; }

/* 动画 */
.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.5s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateY(20px); }
</style>
