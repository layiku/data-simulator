#!/bin/bash

# 检查Python版本
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "错误: 未找到Python3"
  exit 1
fi

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
  echo "初始化虚拟环境..."
  python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 启动服务
echo "启动模拟数据生成器服务..."
python main.py 