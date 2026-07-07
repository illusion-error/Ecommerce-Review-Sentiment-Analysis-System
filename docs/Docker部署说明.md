# Docker 部署说明

## 适用阶段

本文档用于第一阶段“基础可运行版”验收，目标是使用 Docker Compose 启动后端、前端占位页、MySQL 和 Redis。

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
| backend | sentiment-backend | 8000 | FastAPI 后端接口 |
| frontend | sentiment-frontend | 5173 | 第一阶段前端占位页 |
| mysql | sentiment-mysql | 3306 | 保存评论和分析记录 |
| redis | sentiment-redis | 6379 | 缓存重复文本预测结果 |

## 验收地址

后端健康检查：

```text
http://127.0.0.1:8000/api/health
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

前端占位页：

```text
http://127.0.0.1:5173
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

当前前端是 Docker 占位页，用于证明前端服务能被 Compose 启动。正式 Vue3 页面由成员 A 后续补充后，可继续沿用 `frontend/Dockerfile` 做生产构建调整。

当前模型如未接入 BERT，会使用后端规则模型占位，保证接口、数据库、缓存和批量分析流程先跑通。
