<template>
  <div style="padding: 40px; max-width: 1200px; margin: 0 auto;">
    <h1 style="text-align: center; margin-bottom: 30px;">电商评论情感分析系统</h1>
    
    <el-tabs type="border-card" @tab-click="handleTabClick">
      <!-- ================= 模块 1：单条分析 (A-02) ================= -->
      <el-tab-pane label="单条评论分析">
        <el-card shadow="never">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="4"
            placeholder="请输入需要分析的电商评论..."
          />
          <div style="margin-top: 15px; text-align: right;">
            <el-button type="primary" :loading="loadingSingle" @click="handleAnalyzeSingle">
              开始分析
            </el-button>
          </div>
        </el-card>

        <el-card v-if="resultSingle" shadow="never" style="margin-top: 20px; background-color: #f8f9fa;">
          <template #header><strong>分析结果</strong></template>
          <div style="line-height: 2;">
            <p><strong>情感倾向：</strong> 
              <el-tag :type="resultSingle.sentiment === 'positive' ? 'success' : 'danger'" size="large">
                {{ resultSingle.sentiment === 'positive' ? '😊 正向' : '😡 负向' }}
              </el-tag>
            </p>
            <p><strong>AI 置信度：</strong> {{ (resultSingle.confidence * 100).toFixed(2) }}%</p>
            <p><strong>情感强度 (0-10)：</strong> {{ resultSingle.strength }} 分</p>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- ================= 模块 2：批量分析 (A-03) ================= -->
      <el-tab-pane label="批量文件分析">
        <el-card shadow="never">
          <el-upload
            class="upload-demo"
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleMockUpload"
            accept=".csv, .xlsx"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">支持 .csv 或 .xlsx 文件</div>
            </template>
          </el-upload>
        </el-card>

        <el-card v-if="batchResult" shadow="never" style="margin-top: 20px;" v-loading="loadingBatch">
          <template #header><strong>批量分析总结</strong></template>
          <el-descriptions border :column="3">
            <el-descriptions-item label="总记录数">{{ batchResult.total }}</el-descriptions-item>
            <el-descriptions-item label="正向数量"><el-tag type="success">{{ batchResult.positive_count }}</el-tag></el-descriptions-item>
            <el-descriptions-item label="负向数量"><el-tag type="danger">{{ batchResult.negative_count }}</el-tag></el-descriptions-item>
          </el-descriptions>
          <div style="margin-top: 20px; text-align: center;">
            <el-button type="success" @click="handleDownload">下载报告 (CSV)</el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- ================= 模块 4：数据看板 (A-05) 新增！ ================= -->
      <el-tab-pane label="数据统计看板" name="dashboard">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header><strong>正负情感分布</strong></template>
              <div id="pieChart" style="height: 350px;"></div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="hover">
              <template #header><strong>情感强度趋势分布</strong></template>
              <div id="barChart" style="height: 350px;"></div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ================= 模块 3：历史记录 (A-04) ================= -->
      <el-tab-pane label="历史记录查询">
        <el-table :data="historyData" border style="width: 100%" stripe>
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="raw_text" label="原始评论" show-overflow-tooltip />
          <el-table-column prop="sentiment" label="情感" width="100" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.sentiment === 'positive' ? 'success' : 'danger'">
                {{ scope.row.sentiment === 'positive' ? '正向' : '负向' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="strength" label="强度" width="80" />
          <el-table-column prop="time" label="分析时间" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts' // 引入 ECharts

// --- 单条分析 ---
const inputText = ref('')
const loadingSingle = ref(false)
const resultSingle = ref(null)

const handleAnalyzeSingle = () => {
  if (!inputText.value.trim()) return
  loadingSingle.value = true
  setTimeout(() => {
    loadingSingle.value = false
    const isBad = inputText.value.includes('差')
    resultSingle.value = { sentiment: isBad ? 'negative' : 'positive', confidence: 0.9, strength: isBad ? 1.5 : 8.8 }
    ElMessage.success('分析成功！')
  }, 500)
}

// --- 批量分析 ---
const loadingBatch = ref(false)
const batchResult = ref(null)
const handleMockUpload = () => {
  loadingBatch.value = true
  batchResult.value = true
  setTimeout(() => {
    loadingBatch.value = false
    batchResult.value = { total: 100, positive_count: 75, negative_count: 25, avg_strength: 7.2 }
  }, 1000)
}

// --- 历史记录 ---
const historyData = ref([
  { id: 1, raw_text: "东西真的很好用", sentiment: "positive", strength: 9.5, time: "2026-07-07" },
  { id: 2, raw_text: "物流太慢了", sentiment: "negative", strength: 2.1, time: "2026-07-07" },
])

// --- ECharts 图表逻辑 (A-05) ---
let pieChart = null
let barChart = null

const initCharts = () => {
  // 1. 饼图配置
  const pieDom = document.getElementById('pieChart')
  if (pieDom) {
    pieChart = echarts.init(pieDom)
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '5%', left: 'center' },
      color: ['#67C23A', '#F56C6C'], // 绿红配色
      series: [{
        name: '情感占比',
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: 75, name: '正向评论' },
          { value: 25, name: '负向评论' }
        ]
      }]
    })
  }

  // 2. 柱状图配置
  const barDom = document.getElementById('barChart')
  if (barDom) {
    barChart = echarts.init(barDom)
    barChart.setOption({
      xAxis: { type: 'category', data: ['0-2分', '2-4分', '4-6分', '6-8分', '8-10分'] },
      yAxis: { type: 'value' },
      series: [{
        data: [10, 15, 20, 30, 25],
        type: 'bar',
        itemStyle: { color: '#409EFF' }
      }]
    })
  }
}

// 重点：Tabs 切换时，由于 DOM 可能是隐藏的，图表需要重新计算大小
const handleTabClick = (pane) => {
  if (pane.props.name === 'dashboard') {
    // 等待 DOM 渲染完成后再初始化图表
    nextTick(() => {
      initCharts()
    })
  }
}

// 自动适配窗口大小
window.addEventListener('resize', () => {
  pieChart && pieChart.resize()
  barChart && barChart.resize()
})
</script>

<style>
.el-upload-dragger {
  height: 200px !important;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
</style>