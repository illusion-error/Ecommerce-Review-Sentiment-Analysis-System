# 电商评论情感分析系统

基于 BERT、FastAPI、Vue3、MySQL、Redis 和 Docker 的电商评论情感分析系统。系统面向电商评论文本，支持数据清洗、模型训练、单条情感分析、批量文件分析、历史记录查询、结果导出和可视化看板。

## 项目目标

本项目将电商评论从原始文本转化为可分析的情感数据，帮助快速判断用户评论的正向、负向倾向，并通过统计图表展示商品口碑分布和趋势。

核心目标：

- 完成电商评论数据采集、清洗、标注映射和训练集划分。
- 基于 `bert-base-chinese` 微调中文情感二分类模型。
- 提供单条文本和 CSV/Excel 批量评论分析接口。
- 使用 MySQL 保存分析历史，使用 Redis 缓存重复预测结果。
- 使用 Vue3 + ECharts 展示情感分布、时间趋势和历史记录。
- 使用 Docker Compose 管理前端、后端、数据库和缓存服务。

## 功能清单

| 模块 | 功能 |
| --- | --- |
| 数据预处理 | CSV 读取、GBK/UTF-8 容错、URL/空白/非中文字符清洗、重复和异常样本过滤 |
| 数据集划分 | 按 8:1:1 分层划分 train/val/test，保持正负样本比例一致 |
| 模型训练 | BERT 微调、训练日志、评估指标、混淆矩阵、模型保存 |
| 模型优化 | 动态量化、CPU 推理加速、平均响应时间统计 |
| 在线推理 | 单条评论情感分析，输出 label、sentiment、confidence、strength |
| 批量分析 | 上传 CSV/Excel，批量返回每条评论情感和统计汇总 |
| 数据存储 | MySQL 保存评论、预测结果、批次任务和导出记录 |
| 缓存机制 | Redis 缓存重复文本预测结果，降低模型重复推理 |
| 前端可视化 | 单条分析、批量上传、历史查询、情感饼图、趋势图、导出下载 |
| 部署 | Dockerfile、docker-compose.yml、.env.example 一键启动 |

## 技术架构

```text
Vue3 + Element Plus + ECharts
        ↓
FastAPI REST API
        ↓
Sentiment Service
        ↓
BERT / Quantized BERT Inference
        ↓
MySQL 历史数据 + Redis 缓存
        ↓
Docker Compose 部署
```

## 推荐目录结构

```text
Ecommerce-Review-Sentiment-Analysis-System/
├── backend/                       # FastAPI 后端接口
├── frontend/                      # Vue3 前端项目
├── model/                         # 数据处理、训练、推理和模型导出
├── data/
│   ├── raw/                       # 原始评论数据
│   └── processed/                 # 清洗后数据集
├── deployment/                    # Dockerfile、docker-compose、MySQL 初始化脚本
├── docs/                          # 需求说明、分工计划、接口文档、测试报告
├── reports/                       # 训练日志、性能报告、可视化截图
├── tests/                         # 单元测试、接口测试、集成测试
└── .env.example                   # 环境变量模板
```

## 核心接口草案

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 服务健康检查 |
| `POST` | `/api/sentiment/single` | 单条评论情感分析 |
| `POST` | `/api/sentiment/batch` | 上传 CSV/Excel 批量分析 |
| `GET` | `/api/tasks/{task_id}` | 查询批量任务状态 |
| `GET` | `/api/history` | 分页查询分析历史 |
| `GET` | `/api/statistics/summary` | 查询情感统计汇总 |
| `GET` | `/api/export/{task_id}` | 下载批量分析结果 |

## 数据字段规范

清洗后的标准数据集建议包含以下字段：

| 字段 | 含义 |
| --- | --- |
| `product_id` | 商品或商品类别 ID |
| `content` | 原始评论文本 |
| `comment_time` | 评论时间 |
| `star` | 星级评分 |
| `label` | 情感标签，0 为负向，1 为正向 |
| `clean_content` | 清洗后的纯中文评论 |
| `cut_words` | Jieba 分词结果 |

## 运行方式

当前仓库已包含项目文档和工程目录骨架，代码按分工逐步补充。

后续推荐启动方式：

```powershell
copy .env.example .env
docker compose up -d --build
```

本地开发可分别启动：

```powershell
# 后端
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 前端
cd frontend
npm install
npm run dev
```

## 项目文档

- [需求规格说明书](docs/电商评论情感分析系统需求规格说明书_V1.0.md)
- [四人分工与两阶段开发实施文档](docs/四人分工与两阶段开发实施文档.md)

## 验收指标

| 类别 | 指标 |
| --- | --- |
| 数据质量 | `clean_content` 字段无 URL、无空白、无非中文噪声；训练/验证/测试集类别比例保持一致 |
| 模型效果 | 测试集输出 Accuracy、Precision、Recall、F1、混淆矩阵 |
| 推理性能 | 单条文本接口平均响应时间目标 ≤ 500ms，重复文本命中 Redis 缓存 |
| 功能完整性 | 单条分析、批量分析、历史查询、结果导出、可视化图表全部可用 |
| 部署稳定性 | Docker Compose 可启动前端、后端、MySQL、Redis |

## 团队分工

- 成员 A：前端页面与 ECharts 可视化。
- 成员 B：FastAPI 后端、MySQL、Redis、接口联调。
- 成员 C：数据预处理、BERT 微调、模型优化与推理服务。
- 成员 D：Docker 部署、测试体系、性能报告与项目文档归档。

