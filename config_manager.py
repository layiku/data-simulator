import json
import os
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理类，负责读取和管理配置文件"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为'config.json'
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except json.JSONDecodeError:
            raise ValueError(f"配置文件 {self.config_path} 不是有效的JSON格式")
    
    def get_global_settings(self) -> Dict[str, Any]:
        """
        获取全局设置
        
        Returns:
            Dict[str, Any]: 全局设置字典
        """
        return self.config.get("global_settings", {})
    
    def get_objects_config(self) -> Dict[str, Any]:
        """
        获取所有对象配置
        
        Returns:
            Dict[str, Any]: 所有对象的配置字典
        """
        return self.config.get("objects", {})
    
    def get_object_config(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定对象的配置
        
        Args:
            object_name: 对象名称
            
        Returns:
            Optional[Dict[str, Any]]: 对象配置，如果不存在则返回None
        """
        objects = self.get_objects_config()
        return objects.get(object_name) 