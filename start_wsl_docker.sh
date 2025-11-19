#!/bin/bash
echo "🐳 启动WSL Docker开发环境..."

if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker Desktop"
    exit 1
fi

docker-compose -f docker-compose.wsl.yml up -d

echo "⏳ 等待服务启动..."
sleep 10

docker-compose -f docker-compose.wsl.yml ps

echo ""
echo "🎉 WSL Docker环境启动完成!"
echo "🔧 服务信息:"
echo "   - 主应用: http://localhost:8000"
echo "   - 调试端口: localhost:5678"
echo "   - Redis: localhost:6379"