# Docker 部署说明

## 适用阶段

本文档用于第一阶段“基础可运行版”验收，目标是使用 Docker Compose 启动后端、Vue 前端、MySQL 和 Redis。

## 启动前准备

1. 安装并打开 Docker Desktop。
2. 确认 Docker Desktop 显示运行正常。
3. 在项目根目录执行命令。

项目根目录示例：

```powershell
cd C:\Users\BIANJ\Ecommerce-Review-Sentiment-Analysis-System
```

## 环境变量

项目提供 `.env.example` 作为环境变量模板。

如需自定义端口或密码，可复制为 `.env` 后修改：

```powershell
copy .env.example .env
```

如果不复制 `.env`，`docker-compose.yml` 也提供了默认值，可以直接启动。

## 一键启动

```powershell
docker compose up -d --build
```

启动后包含以下服务：

| 服务 | 容器名 | 端口 | 说明 |
| --- | --- | --- | --- |
| backend | sentiment-backend | 18000 | FastAPI 后端接口，容器内部为 8000 |
| frontend | sentiment-frontend | 15173 | Vue 前端页面，容器内部为 80 |
| mysql | sentiment-mysql | 3307 | 保存评论和分析记录，容器内部仍为 3306 |
| redis | sentiment-redis | 6380 | 缓存重复文本预测结果，容器内部为 6379 |

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

## 第一阶段说明

当前前端 Dockerfile 会执行 Vue/Vite 生产构建，并使用 Nginx 托管 `dist` 目录。Nginx 同时将 `/api/` 请求代理到后端容器 `backend:8000`，用于 Docker 环境下的前后端联调。

Docker 后端镜像默认使用轻量 API 依赖，避免在容器构建阶段下载体积很大的 PyTorch/CUDA 包。容器内未放置 BERT 权重时，会使用后端规则兜底模型，保证接口、数据库、缓存和批量分析流程先跑通。

默认宿主机端口使用 `15173`、`18000`、`3307`、`6380`，用于避开本机常见的 Vite、FastAPI、MySQL 和 Redis 端口冲突。如仍需自定义端口，可在 `.env` 中修改 `FRONTEND_PORT`、`SERVER_PORT`、`MYSQL_PORT` 和 `REDIS_PORT`。
