from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from config_manager import ConfigManager
from data_object_manager import DataObjectManager
from data_generator import OrderDataGenerator, SumDataGenerator


class APIServer:
    """API服务类，负责提供REST API接口"""
    
    def __init__(self, config_manager: ConfigManager, object_manager: DataObjectManager):
        """
        初始化API服务
        
        Args:
            config_manager: 配置管理器实例
            object_manager: 数据对象管理器实例
        """
        self.app = FastAPI(
            title="模拟数据生成器",
            description="一个用于生成多种模拟数据的服务系统",
            version="1.0.0"
        )
        self.config_manager = config_manager
        self.object_manager = object_manager
        
        # 添加CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 挂载静态文件
        static_dir = "static"
        if os.path.exists(static_dir):
            self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self) -> None:
        """注册API路由"""
        
        @self.app.get("/favicon.ico")
        async def get_favicon():
            """提供favicon.ico文件"""
            # 如果static目录存在，重定向到静态文件
            if os.path.exists("static/favicon.ico"):
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url="/static/favicon.ico")
            # 否则返回404
            raise HTTPException(status_code=404, detail="Favicon not found")
        
        @self.app.get("/")
        async def get_info() -> Dict[str, Any]:
            """获取服务基本信息"""
            return {
                "name": "模拟数据生成器",
                "version": "1.0.0",
                "description": "一个用于生成多种模拟数据的服务系统",
                "objects_count": len(self.object_manager.get_object_names())
            }
        
        @self.app.get("/api/objects")
        async def get_objects() -> List[str]:
            """获取所有数据对象列表"""
            return self.object_manager.get_object_names()
        
        @self.app.get("/api/data/{object_name}")
        async def get_object_data(object_name: str) -> Dict[str, Any]:
            """获取指定对象的当前数据"""
            generator = self.object_manager.get_object(object_name)
            if not generator:
                raise HTTPException(status_code=404, detail=f"对象 '{object_name}' 不存在")
            
            return generator.get_current_data()
        
        @self.app.get("/api/data")
        async def get_all_data() -> Dict[str, Dict[str, Any]]:
            """获取所有对象的当前数据"""
            return self.object_manager.get_all_current_data()
        
        @self.app.get("/api/data/{object_name}/history")
        async def get_object_history(
            object_name: str, 
            count: Optional[int] = Query(None, description="要获取的数据点数量，默认为全部")
        ) -> List[Dict[str, Any]]:
            """获取指定对象的历史数据"""
            generator = self.object_manager.get_object(object_name)
            if not generator:
                raise HTTPException(status_code=404, detail=f"对象 '{object_name}' 不存在")
            
            # 如果是订单类型，使用支持count参数的方法
            if isinstance(generator, OrderDataGenerator):
                return generator.get_history(count)
            
            # 其他类型则按原来的方式处理
            history = generator.get_history()
            if count is not None and count > 0:
                history = history[-count:]
            
            return history
        
        @self.app.get("/api/orders/{object_name}")
        async def get_orders(
            object_name: str, 
            count: int = Query(10, description="要获取的订单数量，默认为10")
        ) -> List[Dict[str, Any]]:
            """获取指定订单对象的订单数据"""
            generator = self.object_manager.get_object(object_name)
            if not generator:
                raise HTTPException(status_code=404, detail=f"对象 '{object_name}' 不存在")
            
            if not isinstance(generator, OrderDataGenerator):
                raise HTTPException(status_code=400, detail=f"对象 '{object_name}' 不是订单类型")
            
            return generator.get_history(count)
        
        @self.app.get("/api/sum/{object_name}/sources")
        async def get_sum_sources(object_name: str) -> Dict[str, Dict[str, Any]]:
            """获取求和对象的源数据"""
            generator = self.object_manager.get_object(object_name)
            if not generator:
                raise HTTPException(status_code=404, detail=f"对象 '{object_name}' 不存在")
            
            if not isinstance(generator, SumDataGenerator):
                raise HTTPException(status_code=400, detail=f"对象 '{object_name}' 不是求和类型")
            
            return generator.get_source_data()
        
        @self.app.get("/api/config/global")
        async def get_global_config() -> Dict[str, Any]:
            """获取全局配置"""
            return self.config_manager.get_global_settings()
        
        @self.app.get("/api/config/{object_name}")
        async def get_object_config(object_name: str) -> Dict[str, Any]:
            """获取指定对象的配置"""
            config = self.config_manager.get_object_config(object_name)
            if not config:
                raise HTTPException(status_code=404, detail=f"对象 '{object_name}' 不存在")
            
            return config
        
        @self.app.get("/api/config")
        async def get_all_configs() -> Dict[str, Dict[str, Any]]:
            """获取所有对象的配置"""
            return self.object_manager.get_all_object_configs()
    
    def run(self, host: str, port: int) -> None:
        """
        运行API服务
        
        Args:
            host: 主机地址
            port: 端口号
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=port) 