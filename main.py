import os
import signal
import sys
from typing import NoReturn

from config_manager import ConfigManager
from data_object_manager import DataObjectManager
from api_server import APIServer


def signal_handler(sig, frame) -> NoReturn:
    """
    信号处理函数，用于优雅地关闭服务
    
    Args:
        sig: 信号
        frame: 当前帧
    """
    print("\n正在停止服务...")
    # 全局对象在脚本范围内定义
    if 'object_manager' in globals():
        object_manager.stop_all()
    print("服务已停止，再见！")
    sys.exit(0)


def main() -> None:
    """主函数，初始化和启动服务"""
    # 处理信号，支持优雅关闭
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 初始化配置管理器
        config_path = os.environ.get("CONFIG_PATH", "config.json")
        config_manager = ConfigManager(config_path)
        
        # 获取全局配置
        global_settings = config_manager.get_global_settings()
        host = global_settings.get("api_host", "0.0.0.0")  # 默认绑定到所有接口，便于Docker容器使用
        port = int(global_settings.get("api_port", 8000))

        # 初始化数据对象管理器
        global object_manager
        object_manager = DataObjectManager(config_manager)
        
        # 启动所有数据生成器
        object_manager.start_all()

        # 初始化并运行API服务器
        api_server = APIServer(config_manager, object_manager)

        print(f"服务启动成功! 监听地址: http://{host}:{port}")
        print(f"API文档: http://{host}:{port}/docs")
        
        # 运行API服务器（阻塞）
        api_server.run(host, port)
        
    except Exception as e:
        print(f"服务启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 