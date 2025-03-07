@echo off
echo 正在启动模拟数据生成器服务...

REM 检查Python版本
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 错误: 未找到Python
    exit /b 1
)

REM 检查是否已安装依赖
if not exist venv\ (
    echo 初始化虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo 安装依赖...
pip install -r requirements.txt

REM 启动服务
echo 启动模拟数据生成器服务...
python main.py 