# 小说转动漫生成器 - Web 版本

基于原有命令行工具的 Web 架构实现,包含前后端分离的 MVP 版本。

## 📁 项目结构

```
aihack/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/routes/     # API 路由
│   │   ├── services/       # 业务逻辑服务
│   │   ├── models/         # 数据模型
│   │   └── main.py         # FastAPI 应用入口
│   └── requirements.txt
│
├── frontend/               # React 前端
│   ├── public/
│   ├── src/
│   │   ├── components/    # React 组件
│   │   ├── pages/         # 页面
│   │   ├── services/      # API 调用
│   │   └── App.js
│   └── package.json
│
└── novel_to_anime/        # 核心处理模块 (复用)
```

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 1. 启动后端

```bash
cd backend

pip install -r requirements.txt

pip install -r ../requirements.txt

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将在 `http://localhost:8000` 启动

API 文档: `http://localhost:8000/docs`

### 2. 启动前端

```bash
cd frontend

npm install

npm start
```

前端将在 `http://localhost:3000` 启动

## 🎯 功能特性

### 后端 API

- **POST /api/tasks/text** - 提交文本任务
- **POST /api/tasks/url** - 提交 URL 任务
- **GET /api/tasks/{task_id}/status** - 查询任务状态
- **GET /api/tasks/{task_id}/result** - 获取任务结果
- **GET /output/** - 静态文件服务(视频下载)

### 前端界面

- ✅ 文本输入支持
- ✅ URL 输入支持
- ✅ 实时任务进度显示
- ✅ 视频在线预览
- ✅ 视频下载功能

## 📝 API 使用示例

### 提交文本任务

```bash
curl -X POST "http://localhost:8000/api/tasks/text" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一段小说文本...",
    "config": {
      "max_scene_length": 500,
      "image_provider": "stability",
      "tts_provider": "azure"
    }
  }'
```

响应:
```json
{
  "task_id": "uuid-123",
  "status": "pending",
  "message": "任务已创建，正在处理中"
}
```

### 查询任务状态

```bash
curl "http://localhost:8000/api/tasks/{task_id}/status"
```

响应:
```json
{
  "task_id": "uuid-123",
  "status": "processing",
  "progress": 45,
  "current_step": "生成场景图片",
  "total_scenes": 10,
  "processed_scenes": 4
}
```

### 获取任务结果

```bash
curl "http://localhost:8000/api/tasks/{task_id}/result"
```

响应:
```json
{
  "task_id": "uuid-123",
  "status": "completed",
  "video_url": "/output/uuid-123/uuid-123.mp4",
  "scenes": [...],
  "characters": ["角色1", "角色2"]
}
```

## 🔧 配置选项

### 后端配置

在提交任务时可以配置:

```json
{
  "max_scene_length": 500,
  "image_provider": "stability",
  "image_api_key": "YOUR_KEY",
  "tts_provider": "azure",
  "tts_api_key": "YOUR_KEY",
  "scene_duration": 5.0,
  "fps": 30
}
```

### 前端环境变量

创建 `frontend/.env`:

```
REACT_APP_API_URL=http://localhost:8000/api
```

## 🔑 API 密钥配置

后端需要配置 AI 服务的 API 密钥。可以通过以下方式:

1. **环境变量** (推荐):
```bash
export STABILITY_API_KEY="your_key"
export AZURE_TTS_KEY="your_key"
```

2. **配置文件**:
复制 `config.example.json` 到 `config.json` 并填写密钥

## 📊 数据流程

```
用户输入 → 前端提交 → POST /api/tasks/text
    ↓
创建任务 → 返回 task_id → 前端轮询状态
    ↓
后台异步处理 (BackgroundTasks)
    ↓
1. 解析文本
2. 提取角色
3. 生成图片
4. 生成语音
5. 合成视频
    ↓
任务完成 → 前端获取结果 → 播放/下载视频
```

## 🎨 技术栈

### 后端
- **FastAPI** - 现代化的 Python Web 框架
- **Pydantic** - 数据验证
- **Uvicorn** - ASGI 服务器
- **BeautifulSoup4** - HTML 解析(URL 抓取)

### 前端
- **React** - UI 框架
- **Axios** - HTTP 客户端
- **CSS3** - 样式

## ⚠️ 注意事项

### MVP 限制

当前版本为 MVP(最小可行产品),有以下限制:

1. **任务队列**: 使用 FastAPI BackgroundTasks,不支持分布式
2. **持久化**: 任务信息存储在 JSON 文件,非数据库
3. **文件管理**: 输出文件未实现自动清理
4. **并发**: 不建议同时处理大量任务

### 生产环境建议

如需部署到生产环境,建议:

1. 使用 **Celery + Redis** 替代 BackgroundTasks
2. 使用 **PostgreSQL/MySQL** 存储任务信息
3. 使用 **OSS**(对象存储)管理视频文件
4. 添加 **用户认证** 和 **权限管理**
5. 实现 **任务优先级** 和 **资源限制**
6. 添加 **监控和日志系统**

## 🔄 后续扩展

- [ ] 使用 Celery 实现异步任务队列
- [ ] WebSocket 实时推送进度
- [ ] 用户系统和认证
- [ ] 任务历史记录管理
- [ ] 多种动漫风格模板
- [ ] 移动端适配
- [ ] Docker 容器化部署

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!
