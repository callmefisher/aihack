# API 文档

## 概述

本文档详细说明了"听，见" AI故事可视化平台的所有API接口。

**Base URL**: `http://localhost:8000/api`

**API版本**: v1.0.0

---

## 目录

- [WebSocket接口](#websocket接口)
- [REST API接口](#rest-api接口)
- [数据模型](#数据模型)
- [错误码](#错误码)

---

## WebSocket接口

### 1. 实时内容生成

WebSocket连接用于实时生成图片、音频和视频内容。

#### 连接端点

```
ws://localhost:8000/api/ws
```

#### 请求消息格式

##### TTS + 图片生成请求

```json
{
  "action": "tts",
  "text": "这是一个测试文本段落，包含场景和角色描述...",
  "paragraph_number": 1,
  "task_id": "task_123456",
  "sequence_number": 0
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | string | 是 | 操作类型，固定值 "tts" |
| text | string | 是 | 要处理的文本内容 |
| paragraph_number | integer | 是 | 段落编号，从1开始 |
| task_id | string | 是 | 任务ID |
| sequence_number | integer | 否 | 序列号，默认0 |

##### 视频生成请求

```json
{
  "action": "video",
  "image_base64": "base64编码的图片数据...",
  "text": "场景描述文本",
  "paragraph_number": 1,
  "task_id": "task_123456",
  "sequence_number": 0
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | string | 是 | 操作类型，固定值 "video" |
| image_base64 | string | 是 | Base64编码的图片数据 |
| text | string | 是 | 场景描述文本 |
| paragraph_number | integer | 是 | 段落编号 |
| task_id | string | 是 | 任务ID |
| sequence_number | integer | 否 | 序列号，默认0 |

##### 心跳请求

```json
{
  "action": "ping"
}
```

#### 响应消息格式

##### 状态消息

```json
{
  "type": "status",
  "message": "开始处理TTS和图片生成...",
  "paragraph_number": 1,
  "sequence_number": 0
}
```

##### TTS结果

```json
{
  "type": "tts_result",
  "data": {
    "data": "base64编码的音频数据",
    "format": "mp3"
  },
  "text": "处理的文本内容",
  "paragraph_number": 1,
  "sequence_number": 0,
  "sentence_index": 1,
  "total_sentences": 5
}
```

##### 图片生成结果

```json
{
  "type": "image_result",
  "data": {
    "data": [
      {
        "b64_json": "base64编码的图片数据",
        "revised_prompt": "优化后的提示词"
      }
    ]
  },
  "paragraph_number": 1,
  "sequence_number": 0
}
```

##### 视频生成进度

```json
{
  "type": "video_progress",
  "message": "视频生成中... 45%",
  "progress": 45,
  "paragraph_number": 1,
  "sequence_number": 0
}
```

##### 视频生成结果

```json
{
  "type": "video_result",
  "video_url": "https://example.com/video.mp4",
  "paragraph_number": 1,
  "sequence_number": 0
}
```

##### 错误消息

```json
{
  "type": "error",
  "message": "错误描述信息",
  "paragraph_number": 1,
  "sequence_number": 0
}
```

##### 完成消息

```json
{
  "type": "complete",
  "message": "处理完成"
}
```

---

## REST API接口

### 1. 健康检查

检查服务运行状态。

#### 请求

```
GET /health
```

#### 响应

```json
{
  "status": "healthy"
}
```

---

### 2. TTS转换

将文本转换为语音（非流式）。

#### 请求

```
POST /api/tts
```

**Headers**:
```
Content-Type: application/json
X-API-Key: your_api_key (可选)
```

**Body**:
```json
{
  "text": "要转换的文本内容",
  "provider": "qiniu",
  "language": "zh-CN"
}
```

**参数说明**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 要转换的文本，最大5000字符 |
| provider | string | 否 | TTS提供商：azure/openai/baidu/qiniu，默认qiniu |
| language | string | 否 | 语言代码，默认zh-CN |

#### 响应

```json
{
  "success": true,
  "message": "语音生成成功",
  "audio_url": "/api/tts/download/uuid.mp3",
  "audio_filename": "uuid.mp3"
}
```

---

### 3. 图片生成

生成指定场景的图片（REST方式）。

#### 请求

```
POST /api/generate/image
```

**Body**:
```json
{
  "task_id": "task_123",
  "text": "场景描述文本",
  "paragraph_number": 1
}
```

#### 响应

```json
{
  "image_url": "/output/task_123/image_1.png",
  "audio_url": "/output/task_123/audio_1.mp3"
}
```

---

### 4. 视频生成

生成指定场景的视频（REST方式）。

#### 请求

```
POST /api/generate/video
```

**Body**:
```json
{
  "task_id": "task_123",
  "text": "场景描述",
  "paragraph_number": 1,
  "image_url": "/output/task_123/image_1.png"
}
```

#### 响应

```json
{
  "video_url": "/output/task_123/video_1.mp4"
}
```

---

## 数据模型

### TTSRequest

```typescript
interface TTSRequest {
  text: string;           // 要转换的文本
  provider?: string;      // TTS提供商
  language?: string;      // 语言代码
}
```

### WebSocketMessage

```typescript
interface WebSocketMessage {
  action: 'tts' | 'video' | 'ping';
  text?: string;
  image_base64?: string;
  paragraph_number?: number;
  task_id?: string;
  sequence_number?: number;
}
```

### WebSocketResponse

```typescript
interface WebSocketResponse {
  type: 'status' | 'tts_result' | 'image_result' | 'video_progress' | 'video_result' | 'error' | 'complete' | 'pong';
  message?: string;
  data?: any;
  paragraph_number?: number;
  sequence_number?: number;
  progress?: number;
  video_url?: string;
}
```

---

## 错误码

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

### 业务错误码

WebSocket错误消息中的错误类型：

| 错误类型 | 说明 |
|----------|------|
| TEXT_EMPTY | 文本内容为空 |
| IMAGE_EMPTY | 图片数据为空 |
| TTS_FAILED | TTS生成失败 |
| IMAGE_GENERATION_FAILED | 图片生成失败 |
| VIDEO_GENERATION_FAILED | 视频生成失败 |
| LLM_FAILED | LLM处理失败 |
| TIMEOUT | 请求超时 |

---

## 使用示例

### Python示例

```python
import websockets
import json
import asyncio

async def generate_content():
    uri = "ws://localhost:8000/api/ws"
    
    async with websockets.connect(uri) as websocket:
        # 发送TTS请求
        message = {
            "action": "tts",
            "text": "在一个阳光明媚的早晨，小明走进了教室。",
            "paragraph_number": 1,
            "task_id": "task_001"
        }
        await websocket.send(json.dumps(message))
        
        # 接收响应
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data['type'] == 'complete':
                break
            elif data['type'] == 'tts_result':
                print(f"收到TTS结果: 句子 {data['sentence_index']}/{data['total_sentences']}")
            elif data['type'] == 'image_result':
                print(f"收到图片结果")
            elif data['type'] == 'error':
                print(f"错误: {data['message']}")

asyncio.run(generate_content())
```

### JavaScript示例

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws');

ws.onopen = () => {
  // 发送TTS请求
  const message = {
    action: 'tts',
    text: '在一个阳光明媚的早晨，小明走进了教室。',
    paragraph_number: 1,
    task_id: 'task_001'
  };
  ws.send(JSON.stringify(message));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'tts_result':
      console.log(`收到TTS结果: 句子 ${data.sentence_index}/${data.total_sentences}`);
      break;
    case 'image_result':
      console.log('收到图片结果');
      break;
    case 'error':
      console.error('错误:', data.message);
      break;
    case 'complete':
      console.log('处理完成');
      break;
  }
};
```

---

## 性能指标

### 响应时间

| 操作 | 平均响应时间 | 说明 |
|------|--------------|------|
| TTS生成（单句） | 500-1000ms | 取决于文本长度和TTS提供商 |
| 图片生成 | 5-10s | 取决于图片质量和AI服务商 |
| 视频生成 | 30-60s | 取决于视频长度和质量 |

### 并发能力

- WebSocket并发连接：1000+
- REST API QPS：500+

---

## 注意事项

1. **WebSocket连接保持** - 建议实现心跳机制，每30秒发送一次ping消息
2. **超时处理** - 图片和视频生成可能较慢，建议设置60秒以上的超时时间
3. **错误重试** - 遇到临时性错误（如超时）时应实现重试机制
4. **Base64数据** - 传输大量Base64数据时注意内存使用
5. **并发控制** - 单个WebSocket连接建议串行处理任务，避免并发导致的资源竞争

---

## 更新日志

### v1.0.0 (2025-01-25)
- 初始版本发布
- 支持WebSocket实时通信
- 支持TTS、图片、视频生成
- 支持多家AI服务商
