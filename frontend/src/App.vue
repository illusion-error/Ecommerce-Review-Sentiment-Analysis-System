<template>
  <div style="padding: 40px; max-width: 1000px; margin: 0 auto;">
    <h1 style="text-align: center; margin-bottom: 30px;">电商评论情感分析系统</h1>
    
    <el-tabs type="border-card">
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

        <!-- 结果展示区 -->
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

      <!-- ================= 模块 2：批量分析 (A-03 & A-06) ================= -->
      <el-tab-pane label="批量文件分析">
        <el-card shadow="never">
          <!-- 拖拽上传组件 -->
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
              <div class="el-upload__tip">
                支持 .csv 或 .xlsx 文件，建议单次上传不超过 10000 条
              </div>
            </template>
          </el-upload>
        </el-card>

        <!-- 批量分析结果展示 -->
        <el-card v-if="batchResult" shadow="never" style="margin-top: 20px;" v-loading="loadingBatch">
          <template #header><strong>批量分析任务完成</strong></template>
          <el-descriptions border :column="3">
            <el-descriptions-item label="任务 ID">{{ batchResult.task_id }}</el-descriptions-item>
            <el-descriptions-item label="总记录数">{{ batchResult.total }}</el-descriptions-item>
            <el-descriptions-item label="平均强度">{{ batchResult.avg_strength }}</el-descriptions-item>
            <el-descriptions-item label="正向评论">
              <el-tag type="success">{{ batchResult.positive_count }} 条</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="负向评论">
              <el-tag type="danger">{{ batchResult.negative_count }} 条</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          <!-- 导出按钮 (A-06) -->
          <div style="margin-top: 20px; text-align: center;">
            <el-button type="success" @click="handleDownload">下载详细分析报告 (CSV)</el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- ================= 模块 3：历史记录 (A-04) ================= -->
      <el-tab-pane label="历史记录查询">
        <!-- 筛选区 -->
        <div style="margin-bottom: 20px;">
          <el-select v-model="filterSentiment" placeholder="全部情感" style="width: 150px;">
            <el-option label="全部情感" value="" />
            <el-option label="正向 (Positive)" value="positive" />
            <el-option label="负向 (Negative)" value="negative" />
          </el-select>
          <el-button type="primary" style="margin-left: 10px;" @click="handleSearch">搜索</el-button>
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
          <el-table-column prop="confidence" label="置信度" width="100">
            <template #default="scope">
              {{ (scope.row.confidence * 100).toFixed(1) }}%
            </template>
          </el-table-column>
          <el-table-column prop="strength" label="强度" width="80" />
          <el-table-column prop="time" label="分析时间" width="180" />
        </el-table>

        <!-- 分页器 -->
        <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <el-pagination
            background
            layout="prev, pager, next, total"
            :total="100"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue' // 引入上传图标

// ================== 模块 1：单条分析逻辑 ==================
const inputText = ref('')
const loadingSingle = ref(false)
const resultSingle = ref(null)

const handleAnalyzeSingle = () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入评论内容！')
    return
  }
  loadingSingle.value = true
  resultSingle.value = null
  setTimeout(() => {
    loadingSingle.value = false
    const isBad = inputText.value.includes('差') || inputText.value.includes('烂') || inputText.value.includes('退')
    resultSingle.value = {
      sentiment: isBad ? 'negative' : 'positive',
      confidence: Math.random() * 0.2 + 0.8,
      strength: isBad ? 2.1 : 9.5
    }
    ElMessage.success('分析成功！')
  }, 800)
}

// ================== 模块 2：批量分析逻辑 ==================
const loadingBatch = ref(false)
const batchResult = ref(null)

const handleMockUpload = (file) => {
  ElMessage.info(`正在解析文件：${file.name}...`)
  loadingBatch.value = true
  batchResult.value = true // 显示面板并挂起 Loading
  
  // 模拟批量处理 2 秒钟
  setTimeout(() => {
    loadingBatch.value = false
    // 模拟文档 5.2 节要求的返回值
    batchResult.value = {
      task_id: "batch_20260707_001",
      total: 100,
      positive_count: 72,
      negative_count: 28,
      avg_strength: 7.4
    }
    ElMessage.success('批量分析任务完成！')
  }, 2000)
}

const handleDownload = () => {
  ElMessage.success('开始下载报告...')
}

// ================== 模块 3：历史记录逻辑 ==================
const filterSentiment = ref('')
// 模拟一组历史数据
const historyData = ref([
  { id: 1, raw_text: "物流太慢了，等了一个星期都没发货，差评！", sentiment: "negative", confidence: 0.98, strength: 1.2, time: "2026-07-07 10:00:00" },
  { id: 2, raw_text: "做工精致，老婆很喜欢，下次还来买。", sentiment: "positive", confidence: 0.95, strength: 9.1, time: "2026-07-07 10:05:00" },
  { id: 3, raw_text: "一般般吧，习惯好评，性价比不高。", sentiment: "positive", confidence: 0.65, strength: 6.0, time: "2026-07-07 11:20:00" },
  { id: 4, raw_text: "包装破损了，里面的东西也有点划痕。", sentiment: "negative", confidence: 0.88, strength: 3.5, time: "2026-07-07 13:15:00" },
])

const handleSearch = () => {
  ElMessage.info(`模拟查询，条件：${filterSentiment.value || '全部'}`)
}
</script>

<style>
/* 稍微优化一下上传框的高度 */
.el-upload-dragger {
  height: 200px !important;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
</style>