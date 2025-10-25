#!/bin/bash

echo "🚀 启动小说转动漫生成器 - 后端服务"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

echo "📦 安装后端依赖..."
pip install -r requirements.txt
pip install -r ../requirements.txt

echo ""
echo "✅ 依赖安装完成"
echo ""
echo "🎬 启动 FastAPI 服务器..."
echo "   访问 API 文档: http://localhost:8000/docs"
echo "   访问健康检查: http://localhost:8000/health"
echo ""
source ~/.bashrc
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
