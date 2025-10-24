#!/bin/bash

echo "🚀 启动小说转动漫生成器 - 前端应用"
echo ""

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

echo "📦 安装前端依赖..."
npm install

echo ""
echo "✅ 依赖安装完成"
echo ""
echo "🎬 启动 React 开发服务器..."
echo "   应用将在浏览器中自动打开"
echo "   访问地址: http://localhost:3000"
echo ""

npm start
