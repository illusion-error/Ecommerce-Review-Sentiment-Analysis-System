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
        <!-- 筛选区 -->
        <div style="margin-bottom: 20px; display: flex; gap: 10px;">
          <el-select v-model="filterSentiment" placeholder="全部情感" clearable style="width: 150px;">
            <el-option label="正向" value="positive" />
            <el-option label="负向" value="negative" />
          </el-select>
          <!-- 时间选择器 -->
          <el-date-picker
            v-model="filterTime"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 250px;"
          />
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </div>

        <!-- 数据表格 -->
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
          <!-- 留意后端返回的时间字段是 time 还是 created_at -->
          <el-table-column prop="created_at" label="分析时间" width="180" />
          
          <!-- 新增的操作列：详情按钮 -->
          <el-table-column label="操作" width="100" align="center">
            <template #default="scope">
              <el-button size="small" type="primary" link @click="showDetail(scope.row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页器 -->
        <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <el-pagination
            background
            layout="total, prev, pager, next"
            :total="historyTotal"
            v-model:current-page="historyPage"
            v-model:page-size="historyPageSize"
            @current-change="handlePageChange"
          />
        </div>

        <!-- 详情弹窗 -->
        <el-dialog v-model="detailVisible" title="分析详情" width="500px">
          <div style="line-height: 1.8;">
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
          <template #footer>
            <el-button @click="detailVisible = false">关闭</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios' // 确保你已经安装并引入了 axios

// --- 状态变量 ---
const inputText = ref('')
const loadingSingle = ref(false)
const resultSingle = ref(null)
const loadingBatch = ref(false)
const batchResult = ref(null)

// --- 统计数据变量 (给 ECharts 用的) ---
// 先给一些默认值，防止后端没数据时图表空白
const statsData = ref({
  positive: 75,
  negative: 25,
  intensity: [10, 15, 20, 30, 25]
})

// ================== 【新增：onMounted 钩子】 ==================
// 页面加载时自动执行
onMounted(async () => {
  console.log('页面已加载，正在同步后端数据...')
  await refreshStatistics() // 获取统计数据
  await fetchHistory()      // 获取历史列表
})

// 封装一个获取统计数据的函数 (对应文档 5.3 节)
const refreshStatistics = async () => {
  try {
    const res = await axios.get('/api/statistics/summary')
    if (res.data.success) {
      // 把后端返回的真实数字存到变量里
      statsData.value.positive = res.data.data.positive_count
      statsData.value.negative = res.data.data.negative_count
      // 如果后端返回了强度分布，也存进去
      if (res.data.data.intensity_distribution) {
        statsData.value.intensity = res.data.data.intensity_distribution
      }
      console.log('统计数据同步成功')
    }
  } catch (error) {
    console.error('获取统计数据失败，请确认后端接口 /api/statistics/summary 是否可用')
  }
}

// ================== 修复 1：导出下载逻辑 (A-06) ==================
const handleDownload = () => {
  if (!batchResult.value || !batchResult.value.task_id) {
    ElMessage.warning('暂无分析任务可以下载！')
    return
  }
  // 使用浏览器的原生下载功能直接调用后端接口
  window.open(`/api/export/${batchResult.value.task_id}`)
  ElMessage.success('正在下载报告...')
}


// ================== 修复 2：历史记录完整闭环 (A-04) ==================
const historyData = ref([])
// 新增分页和筛选变量
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyTotal = ref(0)
const filterSentiment = ref('')
const filterTime = ref([]) // 存放起止时间 [start, end]

// 新增弹窗变量
const detailVisible = ref(false)
const currentDetail = ref({})

const fetchHistory = async () => {
  try {
    // 构造请求 URL，加入分页参数
    let url = `/api/history?page=${historyPage.value}&page_size=${historyPageSize.value}`
    
    // 如果有情感筛选条件，加进去
    if (filterSentiment.value) {
      url += `&sentiment=${filterSentiment.value}`
    }
    
    // 如果后端支持时间筛选（虽然文档没提，但 UI 留好扩展性）
    if (filterTime.value && filterTime.value.length === 2) {
      url += `&start_time=${filterTime.value[0]}&end_time=${filterTime.value[1]}`
    }

    const res = await axios.get(url)
    if (res.data.success) {
      historyData.value = res.data.data.items || []
      // 同步后端返回的总条数，让分页器生效
      historyTotal.value = res.data.data.total || 0 
    }
  } catch (error) {
    console.log('获取历史记录失败')
  }
}

// 点击搜索按钮
const handleSearch = () => {
  historyPage.value = 1 // 每次搜索从第一页开始
  fetchHistory()
}

// 翻页操作
const handlePageChange = (newPage) => {
  historyPage.value = newPage
  fetchHistory()
}

// 打开详情弹窗
const showDetail = (row) => {
  currentDetail.value = row
  detailVisible.value = true
}
// ============================================================

// --- 修改后的 ECharts 初始化逻辑：使用 statsData.value ---
let pieChart = null
let barChart = null

const initCharts = () => {
  const pieDom = document.getElementById('pieChart')
  if (pieDom) {
    pieChart = echarts.init(pieDom)
    pieChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '5%', left: 'center' },
      color: ['#67C23A', '#F56C6C'],
      series: [{
        name: '情感占比',
        type: 'pie',
        radius: ['40%', '70%'],
        // 【关键】：这里使用了 statsData 里的真实数据
        data: [
          { value: statsData.value.positive, name: '正向评论' },
          { value: statsData.value.negative, name: '负向评论' }
        ]
      }]
    })
  }

  const barDom = document.getElementById('barChart')
  if (barDom) {
    barChart = echarts.init(barDom)
    barChart.setOption({
      xAxis: { type: 'category', data: ['0-2', '2-4', '4-6', '6-8', '8-10'] },
      yAxis: { type: 'value' },
      series: [{
        // 【关键】：这里使用了 statsData 里的强度分布
        data: statsData.value.intensity,
        type: 'bar',
        itemStyle: { color: '#409EFF' }
      }]
    })
  }
}

// 单条分析函数 (加上 async/await)
const handleAnalyzeSingle = async () => {
  if (!inputText.value.trim()) return
  loadingSingle.value = true
  try {
    const res = await axios.post('/api/sentiment/single', { text: inputText.value })
    if (res.data.success) {
      resultSingle.value = res.data.data
      ElMessage.success('分析成功')
      // 分析完后，顺便刷新一下看板数据和历史列表，保证数据是最新的
      refreshStatistics()
      fetchHistory()
    }
  } catch (e) {
    ElMessage.error('分析接口联调失败')
  } finally {
    loadingSingle.value = false
  }
}

// 批量分析上传
const handleMockUpload = async (file) => {
  loadingBatch.value = true
  const formData = new FormData()
  formData.append('file', file.raw)
  try {
    const res = await axios.post('/api/sentiment/batch', formData)
    if (res.data.success) {
      batchResult.value = res.data.data
      ElMessage.success('批量分析成功')
      refreshStatistics() // 刷新看板
    }
  } catch (e) {
    ElMessage.error('批量接口联调失败')
  } finally {
    loadingBatch.value = false
  }
}

// Tabs 切换处理
const handleTabClick = (pane) => {
  if (pane.props.name === 'dashboard') {
    nextTick(() => {
      initCharts()
    })
  }
}

// 自动缩放
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