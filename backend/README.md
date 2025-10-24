# Novel to Anime - Backend API

基于FastAPI的后端API服务，提供文本转语音(TTS)功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（可选）：

```bash
# Azure TTS
TTS_API_KEY=your_azure_tts_key

# 百度 TTS
BAIDU_APP_ID=your_baidu_app_id
BAIDU_SECRET_KEY=your_baidu_secret_key

# OpenAI TTS
# TTS_API_KEY=your_openai_key
```

### 3. 启动服务

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 启动。

## 📖 API 文档

启动服务后，访问以下地址查看自动生成的API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 API 端点

### 1. 文本转语音

**端点**: `POST /api/tts`

**请求体**:
```json
{
  "text": "这是一段测试文本，将被转换为语音。",
  "provider": "azure",
  "language": "zh-CN"
}
```

**参数说明**:
- `text` (必填): 要转换的文本内容，最大5000字符
- `provider` (可选): TTS提供商，支持 `azure`、`openai`、`baidu`，默认 `azure`
- `language` (可选): 语言代码，默认 `zh-CN`

**请求头** (可选):
```
X-API-Key: your_tts_api_key
X-Baidu-App-Id: your_baidu_app_id (使用百度TTS时需要)
X-Baidu-Secret-Key: your_baidu_secret_key (使用百度TTS时需要)
```

**响应**:
```json
{
  "success": true,
  "message": "语音生成成功",
  "audio_url": "/api/tts/download/uuid.mp3",
  "audio_filename": "uuid.mp3"
}
```

### 2. 下载音频文件

**端点**: `GET /api/tts/download/{filename}`

直接返回音频文件流，可在浏览器中播放或下载。

### 3. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy"
}
```

## 📝 使用示例

### curl 示例

```bash
# 使用Azure TTS
curl -X POST "http://localhost:8000/api/tts" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_azure_key" \
  -d '{
    "text": "你好，这是一个测试。",
    "provider": "azure",
    "language": "zh-CN"
  }'

# 使用百度TTS
curl -X POST "http://localhost:8000/api/tts" \
  -H "Content-Type: application/json" \
  -H "X-Baidu-App-Id: your_app_id" \
  -H "X-Baidu-Secret-Key: your_secret_key" \
  -d '{
    "text": "你好，这是一个测试。",
    "provider": "baidu",
    "language": "zh-CN"
  }'
```

### Python 示例

```python
import requests

url = "http://localhost:8000/api/tts"

payload = {
    "text": "这是一段测试文本。",
    "provider": "azure",
    "language": "zh-CN"
}

headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your_api_key"
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    result = response.json()
    print(f"成功! 音频URL: {result['audio_url']}")
    
    audio_url = f"http://localhost:8000{result['audio_url']}"
    audio_response = requests.get(audio_url)
    
    with open("output.mp3", "wb") as f:
        f.write(audio_response.content)
    print("音频已保存到 output.mp3")
else:
    print(f"错误: {response.text}")
```

### JavaScript 示例

```javascript
const url = 'http://localhost:8000/api/tts';

const payload = {
  text: '这是一段测试文本。',
  provider: 'azure',
  language: 'zh-CN'
};

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your_api_key'
  },
  body: JSON.stringify(payload)
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    console.log('成功!', data);
    const audioUrl = `http://localhost:8000${data.audio_url}`;
    // 可以在网页中播放或下载
    window.open(audioUrl, '_blank');
  }
})
.catch(error => console.error('错误:', error));
```

## 🗂️ 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── tts.py          # TTS API路由
│   ├── services/
│   │   ├── __init__.py
│   │   └── tts_service.py      # TTS服务逻辑
│   ├── models/
│   │   ├── __init__.py
│   │   └── tts.py              # 数据模型
│   └── core/
│       ├── __init__.py
│       └── config.py           # 配置管理
├── output/
│   └── audio/                  # 生成的音频文件
├── requirements.txt
└── README.md
```

## 🔑 支持的TTS提供商

### 1. Azure Cognitive Services TTS
- 需要Azure订阅和API密钥
- 高质量语音合成
- 支持多种语言和声音

### 2. OpenAI TTS
- 需要OpenAI API密钥
- 支持 `tts-1` 模型
- 自然流畅的语音

### 3. 百度语音合成
- 需要百度AI开放平台账号
- 需要 App ID 和 Secret Key
- 支持中文语音合成

## ⚠️ 注意事项

1. **API密钥安全**: 不要将API密钥提交到版本控制系统
2. **费用控制**: 使用TTS服务会产生费用，注意控制调用频率
3. **文本长度限制**: 单次请求文本最长5000字符
4. **文件清理**: 生成的音频文件会保存在 `output/audio/` 目录，建议定期清理

## 🧪 测试

访问 http://localhost:8000/docs 使用Swagger UI进行交互式测试。

## 📦 部署

### Docker部署（推荐）

```bash
# 构建镜像
docker build -t novel-to-anime-api .

# 运行容器
docker run -d -p 8000:8000 \
  -e TTS_API_KEY=your_key \
  novel-to-anime-api
```

### 生产环境部署

使用 `gunicorn` + `uvicorn` workers:

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 📄 许可证

MIT License
