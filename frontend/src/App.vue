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
              <h3 style="margin-top:0; color:#f8fafc;">输入单条文本进行情感预测</h3>
              <el-input v-model="inputText" type="textarea" :rows="5" resize="none" placeholder="输入你想测试的商品评论，感受 BERT 模型的威力..." />
              <div style="margin-top: 20px; text-align: right;">
                <el-button type="primary" size="large" round :loading="loadingSingle" @click="handleAnalyzeSingle">
                  <el-icon style="margin-right:5px;"><VideoPlay /></el-icon> 启动推理引擎
                </el-button>
              </div>
            </el-card>

            <transition name="fade-slide">
              <el-card v-if="resultSingle" class="glass-card result-card" shadow="always" style="margin-top: 20px;">
                <template #header><strong style="font-size: 18px; color:#f8fafc;">推理结果</strong></template>
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
                    <span class="value number">{{ resultSingle.strength }}<span style="font-size:14px;color:#94a3b8;">/10</span></span>
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

            <el-table :data="historyData" style="width: 100%; border-radius: 8px; overflow: hidden; margin-top:15px;" class="dark-table">
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

        <!-- ================= 模块 4：批量上传 (放在最后) ================= -->
        <el-tab-pane label="📁 批量处理中心" name="batch">
          <el-card class="glass-card" shadow="never">
            <h3 style="margin-top:0; color:#f8fafc; text-align:center;">上传数据集进行批量分析</h3>
            <el-upload class="upload-demo" drag action="#" :auto-upload="false" :on-change="handleMockUpload" accept=".csv, .xlsx">
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text" style="color:#cbd5e1;">将文件拖到此处，或 <em style="color:#00f2fe;">点击上传</em></div>
              <template #tip><div class="el-upload__tip" style="text-align:center; color:#94a3b8;">支持 .csv 或 .xlsx 文件</div></template>
            </el-upload>
          </el-card>

          <el-card v-if="batchResult" class="glass-card" shadow="never" style="margin-top: 20px;" v-loading="loadingBatch">
            <template #header><strong style="color:#f8fafc;">批量分析总结</strong></template>
            <el-descriptions border :column="3" class="dark-desc">
              <el-descriptions-item label="总记录数">{{ batchResult.total }}</el-descriptions-item>
              <el-descriptions-item label="正向数量"><el-tag type="success">{{ batchResult.positive_count }}</el-tag></el-descriptions-item>
              <el-descriptions-item label="负向数量"><el-tag type="danger">{{ batchResult.negative_count }}</el-tag></el-descriptions-item>
            </el-descriptions>
            <div style="margin-top: 20px; text-align: center;">
              <el-button type="success" round @click="handleDownload">下载详细分析报告 (CSV)</el-button>
            </div>
          </el-card>
        </el-tab-pane>

      </el-tabs>
    </div>

    <!-- 弹窗 -->
    <el-dialog v-model="detailVisible" title="分析详情" width="500px" custom-class="dark-dialog">
      <div style="line-height: 1.8; color: #1e293b;">
        <p><strong>原始文本：</strong> {{ currentDetail.raw_text }}</p>
        <p><strong>清洗文本：</strong> {{ currentDetail.clean_text || '暂无数据' }}</p>
        <p><strong>情感倾向：</strong> 
          <el-tag :type="currentDetail.sentiment === 'positive' ? 'success' : 'danger'">
            {{ currentDetail.sentiment === 'positive' ? '正向' : '负向' }}
          </el-tag>
        </p>
        <p><strong>置信度：</strong> {{ currentDetail.confidence ? (currentDetail.confidence * 100).toFixed(2) + '%' : '暂无数据' }}</p>
        <p><strong>情感强度：</strong> {{ currentDetail.strength }} 分</p>
        <p><strong>分析时间：</strong> {{ currentDetail.created_at || currentDetail.time }}</p>
      </div>
      <template #footer><el-button @click="detailVisible = false">关闭</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Cpu, Trophy, Warning, Star, Search, VideoPlay, UploadFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'
import axios from 'axios'

const activeTab = ref('dashboard')
const inputText = ref('')
const loadingSingle = ref(false)
const resultSingle = ref(null)
const loadingBatch = ref(false)
const batchResult = ref(null)

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

const detailVisible = ref(false)
const currentDetail = ref({})

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

const wordCloudFallback = (text) => [{ name: text, value: 1, textStyle: { color: '#475569' } }]

/* ================= 重点：ECharts 暗黑模式改造 ================= */
const initCharts = () => {
  disposeCharts()

  if (document.getElementById('pieChart')) {
    pieChart = echarts.init(document.getElementById('pieChart'), 'dark') // 开启暗黑
    pieChart.setOption({
      backgroundColor: 'transparent', // 强制透明背景
      tooltip: { trigger: 'item', backgroundColor: 'rgba(30,41,59,0.9)', borderColor: '#334155', textStyle: {color: '#fff'} },
      legend: { bottom: '5%', icon: 'circle', textStyle: { color: '#cbd5e1' } },
      series: [{
        type: 'pie', radius: ['50%', '75%'], center: ['50%', '45%'],
        itemStyle: { borderRadius: 10, borderColor: 'rgba(30,41,59,0.5)', borderWidth: 2 },
        label: { show: false },
        data: [
          { value: statsData.value.positive, name: '正向 (Positive)', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: '#43E97B'}, {offset: 1, color: '#38F9D7'}]) } },
          { value: statsData.value.negative, name: '负向 (Negative)', itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: '#FA709A'}, {offset: 1, color: '#FEE140'}]) } }
        ]
      }]
    })
  }

  if (document.getElementById('barChart')) {
    barChart = echarts.init(document.getElementById('barChart'), 'dark')
    barChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(30,41,59,0.9)', borderColor: '#334155', textStyle: {color: '#fff'} },
      grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
      xAxis: { type: 'category', data: ['极度不满(0-2)', '偏负向(2-4)', '中立(4-6)', '偏正向(6-8)', '极度满意(8-10)'], axisLine: { lineStyle: { color: '#64748b' } } },
      yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: 'rgba(255,255,255,0.1)' } } },
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
      { name: '价格', score: 0 }, { name: '物流', score: 0 }, { name: '质量', score: 0 }
    ]
    radarChart = echarts.init(document.getElementById('radarChart'), 'dark')
    radarChart.setOption({
      backgroundColor: 'transparent',
      tooltip: { backgroundColor: 'rgba(30,41,59,0.9)', borderColor: '#334155', textStyle: {color: '#fff'} },
      radar: { indicator: radarItems.map(item => ({ name: item.name, max: 100 })), radius: '60%', splitArea: { show: false }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } } },
      series: [{
        type: 'radar',
        data: [{ value: radarItems.map(item => item.score), name: '口碑评分' }],
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: 'rgba(0, 242, 254, 0.4)'}, {offset: 1, color: 'rgba(0, 242, 254, 0.1)'}]) },
        itemStyle: { color: '#00f2fe', borderColor: '#00f2fe', borderWidth: 2 },
        lineStyle: { width: 3, color: '#00f2fe' }
      }]
    })
  }

  if (document.getElementById('posWordCloud')) {
    posWordCloud = echarts.init(document.getElementById('posWordCloud')) // 词云本身不需要暗黑模式配置，背景设透明即可
    posWordCloud.setOption({
      backgroundColor: 'transparent',
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
      backgroundColor: 'transparent',
      series: [{
        type: 'wordCloud', shape: 'circle', gridSize: 8, sizeRange: [16, 60], rotationRange: [0, 0],
        textStyle: { color: () => 'rgb(' + [Math.round(Math.random() * 105 + 150), Math.round(Math.random() * 50), Math.round(Math.random() * 50)].join(',') + ')' },
        data: negWords.value.length ? negWords.value : wordCloudFallback('暂无负向词')
      }]
    })
  }
}

// ================== 其余逻辑接口调用 (保持原样) ==================
const handleAnalyzeSingle = async () => {
  const text = inputText.value.trim()
  if (!text) { ElMessage.warning('请输入评论文本'); return }
  loadingSingle.value = true
  try {
    const response = await axios.post('/api/sentiment/single', { text, product_id: 'web-single' })
    resultSingle.value = response.data.data
    ElMessage.success(`推理完成，情感结果：${resultSingle.value.sentiment}`)
    await fetchAllDashboardData()
    await fetchHistory()
  } catch (error) {
    console.error(error); ElMessage.error('单条分析失败，请检查后端服务')
  } finally {
    loadingSingle.value = false
  }
}

const handleMockUpload = async (file) => {
  loadingBatch.value = true
  const formData = new FormData()
  formData.append('file', file.raw)
  try {
    const res = await axios.post('/api/sentiment/batch', formData)
    if (res.data.success) {
      batchResult.value = res.data.data
      ElMessage.success('批量分析成功')
      await fetchAllDashboardData() 
      await fetchHistory()
    }
  } catch (e) { ElMessage.error('批量接口联调失败') } 
  finally { loadingBatch.value = false }
}

const handleDownload = () => {
  if (!batchResult.value || !batchResult.value.task_id) return
  window.open(`/api/export/${batchResult.value.task_id}`)
  ElMessage.success('正在下载报告...')
}

const fetchHistory = async () => {
  try {
    const params = { page: historyPage.value, page_size: historyPageSize.value }
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
    console.error(error); ElMessage.error('历史记录加载失败')
  }
}

const handleSearch = async () => { historyPage.value = 1; await fetchHistory() }
const handlePageChange = async (page) => { historyPage.value = page; await fetchHistory() }
const showDetail = (row) => { currentDetail.value = row; detailVisible.value = true }

const handleTabClick = (pane) => {
  if (pane.props.name === 'dashboard') { nextTick(() => { initCharts() }) }
  if (pane.props.name === 'history') { fetchHistory() }
}

const resizeCharts = () => {
  pieChart?.resize(); barChart?.resize(); radarChart?.resize(); posWordCloud?.resize(); negWordCloud?.resize();
}

window.addEventListener('resize', resizeCharts)
</script>

<style>
/* ================== 赛博深渊暗黑风 + 全息毛玻璃 UI ================== */
body {
  /* 极具深度的暗夜蓝紫渐变背景 */
  background: radial-gradient(circle at 50% 0%, #1e293b 0%, #0f172a 50%, #020617 100%);
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', Arial, sans-serif;
  color: #f8fafc;
}
.app-container { padding: 30px; max-width: 1300px; margin: 0 auto; }

/* 炫酷渐变标题 */
.app-header { text-align: center; margin-bottom: 40px; }
.logo-box { display: flex; align-items: center; justify-content: center; gap: 15px; }
.logo-icon { font-size: 36px; color: #00f2fe; filter: drop-shadow(0 0 8px rgba(0,242,254,0.6)); }
.gradient-text {
  font-size: 32px; font-weight: 800; margin: 0;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
  -webkit-background-clip: text; color: transparent;
  letter-spacing: 2px;
}
.version-tag {
  font-size: 13px; background: rgba(0, 242, 254, 0.1); color: #00f2fe;
  border: 1px solid rgba(0, 242, 254, 0.3); padding: 4px 10px; border-radius: 20px; vertical-align: middle;
}
.subtitle { color: #94a3b8; letter-spacing: 1px; margin-top: 10px; }

/* 导航 Tabs 暗黑悬浮态 */
.modern-tabs > .el-tabs__header {
  background: rgba(30, 41, 59, 0.4); backdrop-filter: blur(12px);
  padding: 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);
}
.modern-tabs > .el-tabs__header .el-tabs__nav { border: none !important; }
.modern-tabs > .el-tabs__header .el-tabs__item {
  border: none !important; font-size: 16px; font-weight: 600; color: #94a3b8;
  border-radius: 8px; margin: 0 5px; transition: all 0.3s;
}
.modern-tabs > .el-tabs__header .el-tabs__item.is-active {
  background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); color: #fff;
  box-shadow: 0 4px 15px rgba(0, 242, 254, 0.4);
}
/* 去掉底部的默认蓝线 */
.modern-tabs > .el-tabs__header .el-tabs__active-bar { display: none; }
.modern-tabs { background: transparent !important; border: none !important; }
.modern-tabs > .el-tabs__content { padding: 20px 0 !important; }

/* 核心：暗黑全息毛玻璃卡片 */
.glass-card {
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 16px;
  background: rgba(30, 41, 59, 0.5) !important; /* 半透明暗板 */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}
.glass-card:hover {
  transform: translateY(-5px);
  border-color: rgba(0, 242, 254, 0.3) !important;
  box-shadow: 0 12px 40px rgba(0, 242, 254, 0.15);
}

/* 卡片内部文字适配暗黑 */
.el-card__header { border-bottom: 1px solid rgba(255,255,255,0.05) !important; }
.chart-title, .ai-title { color: #f8fafc !important; font-size: 16px; letter-spacing: 1px; }
.ai-card { border-left: 6px solid #00f2fe !important; }
.insight-box h4 { margin-top: 0; font-size: 16px; display: flex; align-items: center; gap: 6px; }
.positive-box h4 { color: #43e97b; }
.negative-box h4 { color: #ff0844; }
.advice-box h4 { color: #f6d365; }
.insight-box ul { padding-left: 20px; color: #cbd5e1; line-height: 1.8; }
.insight-box p { color: #cbd5e1; line-height: 1.8; padding-left: 5px; }
.text-green { color: #43e97b !important; }
.text-red { color: #ff0844 !important; }

/* 交互区输入框改造 */
.el-textarea__inner {
  background: rgba(15, 23, 42, 0.6) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  color: #f8fafc !important;
  border-radius: 8px;
}
.el-textarea__inner:focus { border-color: #00f2fe !important; box-shadow: 0 0 8px rgba(0,242,254,0.3); }

/* 推理结果面板 */
.result-grid { display: flex; justify-content: space-around; padding: 20px 0; }
.result-item { text-align: center; }
.result-item .label { display: block; color: #94a3b8; margin-bottom: 10px; font-size: 14px; }
.result-item .value.number { font-size: 28px; font-weight: bold; color: #00f2fe; }

/* ================== 历史表格白底黑字清晰改造 ================== */
.filter-bar { display: flex; gap: 15px; margin-bottom: 20px; }
.dark-table {
  background-color: #fff !important;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.dark-table th.el-table__cell { 
  color: #1e293b !important; /* 深黑色表头文字 */
  background-color: #f1f5f9 !important; /* 浅灰表头背景 */
  border-bottom: 1px solid #e2e8f0 !important; 
  font-weight: bold; 
}
.dark-table td.el-table__cell { 
  color: #334155 !important; /* 深黑色正文文字 */
  background-color: #fff !important;
  border-bottom: 1px solid #f1f5f9 !important; 
}
/* 斑马纹交替色 */
.dark-table.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell { 
  background: #f8fafc !important; 
}
/* 鼠标悬浮高亮变青色 */
.dark-table tbody tr:hover > td.el-table__cell {
  background-color: #e0f2fe !important;
}

/* ================== 底部分页条白底黑字改造 ================== */
.el-pagination.is-background .el-pager li:not(.is-disabled).is-active { 
  background-color: #00f2fe !important; 
  color: #0f172a !important; 
  font-weight: bold;
}
.el-pagination.is-background .el-pager li { 
  background-color: #fff !important; 
  color: #334155 !important; 
  border: 1px solid #e2e8f0;
}
.el-pagination.is-background .btn-next, .el-pagination.is-background .btn-prev { 
  background-color: #fff !important; 
  color: #334155 !important; 
  border: 1px solid #e2e8f0;
}
.el-pagination__total, .el-pagination__jump {
  color: #94a3b8 !important;
}

/* 图表容器 */
.chart-row { margin-bottom: 24px; }
.chart-container { height: 320px; }

/* 动画 */
.fade-slide-enter-active, .fade-slide-leave-active { transition: all 0.5s ease; }
.fade-slide-enter-from { opacity: 0; transform: translateY(20px); }
</style>