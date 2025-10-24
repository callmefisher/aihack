# 小说转动漫生成器 (Novel to Anime Generator)

一个能够将小说文本自动转换为动漫视频的工具，生成的视频包含场景图片、文字和语音旁白。

## ✨ 功能特点

- 📖 **智能场景分割**: 自动将小说文本分割为多个场景
- 🎨 **AI图像生成**: 使用Stability AI或OpenAI DALL-E生成动漫风格的场景插图
- 🎤 **文字转语音**: 支持Azure TTS和OpenAI TTS，生成自然的语音旁白
- 🎬 **视频合成**: 自动将图片、文字和语音合成为完整的视频
- 🛠️ **灵活配置**: 支持多种AI服务提供商，可自定义各种参数

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

复制配置文件模板并填入你的API密钥：

```bash
cp config.example.json config.json
```

编辑 `config.json`：

```json
{
  "max_scene_length": 500,
  "image_provider": "stability",
  "image_api_key": "YOUR_STABILITY_AI_KEY",
  "tts_provider": "azure",
  "tts_api_key": "YOUR_AZURE_TTS_KEY",
  "scene_duration": 5.0,
  "fps": 30
}
```

### 3. 运行示例

```bash
python novel_to_anime.py example_novel.txt -c config.json -o output -n my_anime.mp4
```

## 📖 使用说明

### 基本用法

```bash
python novel_to_anime.py <小说文件路径> [选项]
```

### 命令行选项

- `-o, --output <目录>`: 指定输出目录（默认: `output`）
- `-n, --name <文件名>`: 指定输出视频文件名（默认: `anime.mp4`）
- `-c, --config <配置文件>`: 指定JSON格式的配置文件

### 示例

生成动漫视频：
```bash
python novel_to_anime.py my_novel.txt -o ./results -n story.mp4
```

使用自定义配置：
```bash
python novel_to_anime.py my_novel.txt -c my_config.json
```

## 🎯 工作流程

1. **文本解析**: 读取小说文本，按段落和长度智能分割场景
2. **场景提取**: 提取每个场景的叙述文字和对话内容
3. **图像生成**: 根据场景描述生成动漫风格的插图
4. **语音合成**: 将场景文字转换为语音旁白
5. **视频合成**: 将图片、文字和语音组合成视频

## 🔧 配置选项

### 图像生成

支持的提供商：
- `stability`: Stability AI (推荐)
- `openai`: OpenAI DALL-E

### 语音合成

支持的提供商：
- `azure`: Azure Cognitive Services TTS (推荐)
- `openai`: OpenAI TTS

### 其他选项

- `max_scene_length`: 每个场景的最大文字长度（字符数）
- `scene_duration`: 默认场景持续时间（秒）
- `fps`: 视频帧率

## 📁 输出文件

运行后，输出目录将包含：

```
output/
├── scene_001.png          # 场景1的图片
├── scene_001.mp3          # 场景1的语音
├── scene_002.png          # 场景2的图片
├── scene_002.mp3          # 场景2的语音
├── ...
├── scenes_metadata.json   # 场景元数据
└── anime.mp4              # 最终视频
```

## 🔑 获取API密钥

### Stability AI
1. 访问 [Stability AI Platform](https://platform.stability.ai/)
2. 注册账号并获取API密钥
3. 将密钥填入配置文件的 `image_api_key`

### Azure TTS
1. 访问 [Azure Portal](https://portal.azure.com/)
2. 创建认知服务资源
3. 获取订阅密钥
4. 将密钥填入配置文件的 `tts_api_key`

### OpenAI
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 创建API密钥
3. 可用于图像生成或TTS

## ⚠️ 注意事项

- 使用AI服务会产生费用，请注意控制成本
- 生成时间取决于场景数量和AI服务响应速度
- 建议先用短篇小说测试
- 如果没有配置API密钥，程序将生成占位符图片和静音音频用于测试

## 🛠️ 代码架构

项目包含以下核心模块：

- `NovelParser`: 小说文本解析和场景分割
- `ImageGenerator`: AI图像生成（支持多个提供商）
- `TextToSpeech`: 文字转语音（支持多个提供商）
- `VideoComposer`: 视频合成和渲染
- `NovelToAnimeConverter`: 主控制器，协调整个转换流程

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系方式

如有问题或建议，请在GitHub上提出Issue。