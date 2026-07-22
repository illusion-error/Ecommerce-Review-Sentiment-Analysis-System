# 电商评论情感分析系统

电商评论情感分析系统是一个面向商品评论文本的 AI 分析平台。系统基于 `BERT / 规则兜底模型`、`FastAPI`、`Vue3`、`ECharts`、`MySQL`、`Redis` 和 `Docker Compose` 构建，支持单条评论分析、批量文件分析、历史记录检索、统计看板、词云、维度雷达图、商品优缺点总结和结果导出。

项目既可以作为完整 Web 应用运行，也可以作为中文情感分析、评论洞察和接口服务开发的参考工程。

## 核心能力

| 模块 | 说明 |
| --- | --- |
| 单条情感分析 | 输入一条商品评论，返回情感类别、置信度、情绪强度和缓存状态 |
| 批量评论分析 | 上传 CSV 或 Excel 文件，批量生成每条评论的情感结果和批次统计 |
| 历史记录检索 | 支持分页、情感类别、商品 ID、时间范围筛选 |
| 数据统计看板 | 展示正负向占比、情感强度分布和多维评价雷达图 |
| 高频词云 | 按正向、负向评论分别统计高频词，用于观察用户关注点 |
| 维度评分 | 基于价格、物流、质量关键词规则生成商品评价雷达数据 |
| 商品总结 | 根据词云和维度评分生成核心优点、主要槽点和购买建议 |
| 结果导出 | 支持按批次导出 CSV 或 Excel 分析结果 |
| 缓存机制 | Redis 缓存重复评论预测结果，Redis 不可用时自动使用内存缓存 |
| 容器化部署 | 使用 Docker Compose 一键启动前端、后端、MySQL 和 Redis |

## 技术架构

```text
浏览器 / Vue3 + Element Plus + ECharts
        ↓
Nginx 静态资源服务与 /api 反向代理
        ↓
FastAPI 后端接口
        ↓
情感分析服务
        ├── BERT 推理接口
        └── 规则兜底模型
        ↓
评论洞察模块
        ├── 高频词统计
        ├── 价格 / 物流 / 质量维度评分
        └── 商品优缺点总结
        ↓
MySQL 持久化 + Redis 缓存
        ↓
Docker Compose 统一编排
```

## 项目目录

```text
Ecommerce-Review-Sentiment-Analysis-System/
├── backend/                       # FastAPI 后端服务
│   ├── main.py                    # API 入口：单条、批量、历史、统计、洞察、导出
│   ├── database.py                # MySQL / SQLite 数据访问层
│   ├── cache.py                   # Redis / 内存缓存封装
│   ├── sentiment.py               # 情感推理入口与规则兜底逻辑
│   ├── schemas.py                 # 请求与响应数据结构
│   └── settings.py                # 环境变量与运行配置
├── frontend/                      # Vue3 前端应用
│   ├── src/App.vue                # 主页面：看板、推理、历史、批量处理
│   ├── src/api/                   # 前端请求封装
│   ├── Dockerfile                 # 前端构建与 Nginx 部署
│   └── nginx.conf                 # 静态服务与后端代理配置
├── model/                         # 数据处理、模型训练、推理和文本洞察
│   ├── data_preprocess.py         # 原始评论清洗与数据集划分
│   ├── train.py                   # BERT 微调训练脚本
│   ├── predict.py                 # 模型推理封装
│   ├── text_insights.py           # 词云、维度评分、规则总结
│   ├── performance_test.py        # 模型性能测试脚本
│   ├── resources/                 # 停用词等资源文件
│   └── weights/                   # 模型权重目录
├── data/
│   ├── raw/                       # 原始评论数据
│   ├── processed/                 # 清洗后的 train / val / test 数据
│   └── demo/                      # 可直接用于批量测试的示例文件
├── deployment/
│   └── mysql/init.sql             # MySQL 建库建表脚本
├── docs/                          # 需求、接口、部署、测试和汇报文档
├── reports/                       # 模型评估、性能报告和运行截图
├── tests/                         # 后端接口与文本洞察自动化测试
├── docker-compose.yml             # 前端、后端、MySQL、Redis 编排配置
├── pytest.ini                     # pytest 配置
├── .env.example                   # 环境变量模板
└── README.md                      # 项目说明
```

## 前端页面

默认前端地址：

```text
http://127.0.0.1:15173
```

页面包含 4 个主要功能区：

| 页面 | 功能 |
| --- | --- |
| 深度数据洞察大屏 | 展示 AI 评论总结、总体情感分布、情感强度趋势、维度雷达图、正负向词云 |
| 实时推理沙箱 | 输入单条评论并实时返回情感极性、置信度和情绪强度 |
| 知识库与检索 | 查询历史评论分析记录，支持情感类别和时间范围筛选 |
| 批量处理中心 | 上传 CSV / Excel 评论文件，查看批量分析统计，并下载导出结果 |

## 核心接口

默认后端地址：

```text
http://127.0.0.1:18000
```

Swagger 文档：

```text
http://127.0.0.1:18000/docs
```

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 服务健康检查 |
| `POST` | `/api/sentiment/single` | 单条评论情感分析 |
| `POST` | `/api/sentiment/batch` | 上传 CSV / Excel 批量分析 |
| `GET` | `/api/tasks/{task_id}` | 查询批量任务状态 |
| `GET` | `/api/history` | 查询历史分析记录 |
| `GET` | `/api/statistics/summary` | 查询情感统计汇总 |
| `GET` | `/api/export/{task_id}` | 下载批量分析结果 |
| `GET` | `/api/insights/keywords` | 查询正向、负向高频词 |
| `GET` | `/api/insights/aspects` | 查询价格、物流、质量维度评分 |
| `GET` | `/api/summary/product` | 生成商品优缺点和购买建议 |

## 快速启动

运行前请先启动 Docker Desktop。

```powershell
copy .env.example .env
docker compose up -d --build
docker compose ps
```

启动成功后访问：

```text
前端页面：http://127.0.0.1:15173
后端健康检查：http://127.0.0.1:18000/api/health
后端接口文档：http://127.0.0.1:18000/docs
```

正常情况下，`docker compose ps` 会看到 4 个服务：

| 服务 | 容器 | 端口 | 说明 |
| --- | --- | --- | --- |
| frontend | `sentiment-frontend` | `15173 -> 80` | Vue 前端页面 |
| backend | `sentiment-backend` | `18000 -> 8000` | FastAPI 后端接口 |
| mysql | `sentiment-mysql` | `3307 -> 3306` | 分析记录持久化 |
| redis | `sentiment-redis` | `6380 -> 6379` | 重复预测缓存 |

## 使用示例

### 单条评论分析

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:18000/api/sentiment/single" `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"text":"这个手机质量很好，物流很快，价格也很划算，使用体验非常满意。","product_id":"phone"}'
```

返回数据包含：

```json
{
  "sentiment": "positive",
  "confidence": 0.98,
  "strength": 9.8,
  "cached": false
}
```

### 批量评论分析

项目内置示例文件：

```text
data/demo/demo_comments.csv
```

命令行上传：

```powershell
curl.exe -F "file=@data/demo/demo_comments.csv;type=text/csv" `
  -F "product_id=phone" `
  http://127.0.0.1:18000/api/sentiment/batch
```

返回数据包含：

```json
{
  "task_id": "batch_xxxxxxxxxxxx",
  "total": 36,
  "success_count": 36,
  "failed_count": 0,
  "positive_count": 22,
  "negative_count": 14
}
```

### 导出批量结果

将 `{task_id}` 替换为批量分析接口返回的真实值：

```text
http://127.0.0.1:18000/api/export/{task_id}?file_type=csv
http://127.0.0.1:18000/api/export/{task_id}?file_type=xlsx
```

## 数据格式

批量上传文件建议包含以下字段：

| 字段 | 是否必需 | 含义 |
| --- | --- | --- |
| `content` | 推荐 | 评论正文 |
| `product_id` | 可选 | 商品或商品类别 ID |
| `comment_time` | 可选 | 评论时间 |
| `star` | 可选 | 星级评分 |

批量接口会优先读取 `content` 字段。如果文件没有 `content` 字段，会尝试读取 `comment`、`text`、`raw_text`、`评论`、`评价`、`评论内容` 等常见列名。

## 数据存储

MySQL 初始化脚本位于：

```text
deployment/mysql/init.sql
```

主要数据表：

| 表名 | 说明 |
| --- | --- |
| `comments` | 原始评论基础信息 |
| `analysis_records` | 每条评论的情感分析结果 |
| `batch_tasks` | 批量分析任务状态与统计 |

本地测试也支持 SQLite，便于在没有 MySQL 服务时运行自动化测试。

## 模型与推理

系统推理入口位于：

```text
backend/sentiment.py
```

推理逻辑：

1. 优先尝试调用 `model.predict.predict_sentiment`。
2. 如果模型权重或深度学习依赖不可用，自动切换到规则兜底模型。
3. 规则兜底模型会根据正负向关键词计算 `sentiment`、`confidence` 和 `strength`，保证接口和前端页面始终可运行。

模型训练与评估脚本位于：

```text
model/train.py
model/performance_test.py
```

## 测试与验收

### 后端自动化测试

```powershell
docker compose run --rm --no-deps -e DATABASE_BACKEND=sqlite backend python -m pytest -q
```

预期结果：

```text
5 passed
```

### Docker 部署检查

```powershell
docker compose config
docker compose up -d --build
docker compose ps
```

预期结果：

- Compose 配置无语法错误。
- 前端、后端、MySQL、Redis 均可启动。
- MySQL 状态为 `healthy`。
- `http://127.0.0.1:15173` 可访问。
- `http://127.0.0.1:18000/api/health` 返回 `status=ok`。

## 常见问题

### 1. 访问 `127.0.0.1:15173` 打不开

先确认 Docker Desktop 已启动，再执行：

```powershell
docker version
docker compose ps
```

如果 `docker version` 没有 `Server` 信息，说明 Docker daemon 还没有启动完成。

### 2. 批量上传后看板没有变化

刷新前端页面，或回到“深度数据洞察大屏”标签页。看板数据来自后端真实接口和数据库历史记录。

### 3. 中文在 PowerShell 输出里显示乱码

这是 Windows 控制台编码问题，不代表接口数据错误。浏览器页面和 Swagger 文档一般可以正常显示中文。

### 4. 没有 BERT 权重还能运行吗

可以。后端会自动使用规则兜底模型，保证单条分析、批量分析、历史记录、看板、词云、雷达图和总结接口都能正常演示。需要复现 BERT 模型效果时，再补充模型权重并运行训练/评估脚本。

## 项目文档

| 文档 | 路径 |
| --- | --- |
| 需求规格说明书 | `docs/电商评论情感分析系统需求规格说明书_V1.0.md` |
| 接口文档 | `docs/接口文档.md` |
| 后端接口文档 | `docs/后端接口文档.md` |
| Docker 部署说明 | `docs/Docker部署说明.md` |
| 测试用例清单 | `docs/测试用例清单.md` |
| 模型性能报告 | `reports/model_performance_report.md` |

## 团队分工

| 成员 | 负责内容 |
| --- | --- |
| 成员 A | Vue3 前端页面、Element Plus 交互、ECharts 可视化、词云与雷达图展示 |
| 成员 B | FastAPI 后端接口、MySQL 数据库、Redis 缓存、批量处理、导出和接口联调 |
| 成员 C | 数据预处理、BERT 微调、模型评估、推理封装和文本洞察算法 |
| 成员 D | Docker 部署、自动化测试、性能报告、项目文档与归档 |

## 运行状态参考

最近一次本地检查结果：

```text
docker compose up -d --build：通过
docker compose ps：frontend / backend / mysql / redis 均运行
GET /api/health：status=ok
POST /api/sentiment/single：通过
POST /api/sentiment/batch：36 条示例评论全部处理成功
GET /api/statistics/summary：通过
GET /api/insights/keywords：通过
GET /api/insights/aspects：通过
GET /api/summary/product：通过
GET /api/export/{task_id}：通过
pytest：5 passed
```
