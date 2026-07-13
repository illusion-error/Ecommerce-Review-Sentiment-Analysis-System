# Docker 部署说明

## 适用阶段

本文档用于第二阶段验收，目标是使用 Docker Compose 启动后端、Vue 前端、MySQL 和 Redis，并验证评论洞察接口可用。

## 启动前准备

1. 安装并打开 Docker Desktop。
2. 确认 Docker Desktop 显示运行正常。
3. 在项目根目录执行命令。

项目根目录示例：

```powershell
cd C:\Users\BIANJ\Ecommerce-Review-Sentiment-Analysis-System
```

## 一键启动

```powershell
docker compose up -d --build
```

启动后包含以下服务：

| 服务 | 容器名 | 本机端口 | 容器端口 | 说明 |
| --- | --- | --- | --- | --- |
| backend | sentiment-backend | 18000 | 8000 | FastAPI 后端接口 |
| frontend | sentiment-frontend | 15173 | 80 | Vue 前端页面 |
| mysql | sentiment-mysql | 3307 | 3306 | 保存评论和分析记录 |
| redis | sentiment-redis | 6380 | 6379 | 缓存重复文本预测结果 |

## 验收地址

后端健康检查：

```text
http://127.0.0.1:18000/api/health
```

接口文档：

```text
http://127.0.0.1:18000/docs
```

前端页面：

```text
http://127.0.0.1:15173
```

前端代理健康检查：

```text
http://127.0.0.1:15173/api/health
```

## 演示数据导入

```powershell
curl.exe -F "file=@data/demo/demo_comments.csv;type=text/csv" -F "product_id=phone" http://127.0.0.1:18000/api/sentiment/batch
```

导入后可验证第二阶段接口：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:18000/api/insights/keywords?product_id=phone&top_k=10"
Invoke-RestMethod -Uri "http://127.0.0.1:18000/api/insights/aspects?product_id=phone"
Invoke-RestMethod -Uri "http://127.0.0.1:18000/api/summary/product?product_id=phone"
```

## 常用命令

查看容器状态：

```powershell
docker compose ps
```

查看后端日志：

```powershell
docker compose logs backend
```

停止服务：

```powershell
docker compose down
```

清理数据卷后重新初始化数据库：

```powershell
docker compose down -v
docker compose up -d --build
```

## 第二阶段说明

当前前端 Dockerfile 会执行 Vue/Vite 生产构建，并使用 Nginx 托管 `dist` 目录。Nginx 同时将 `/api/` 请求代理到后端容器 `backend:8000`，用于 Docker 环境下的前后端联调。

后端 Dockerfile 使用 `backend/requirements-api.txt`，避免把训练阶段的大模型依赖放入 API 镜像，降低构建成本。
