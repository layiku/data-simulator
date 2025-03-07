from typing import Dict, Any, List, Optional
import threading

from config_manager import ConfigManager
from data_generator import BaseDataGenerator, create_data_generator, SumDataGenerator


class DataObjectManager:
    """数据对象管理类，负责管理多个数据对象"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化数据对象管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        print("初始化DataObjectManager开始...")
        self.config_manager = config_manager
        self.objects: Dict[str, BaseDataGenerator] = {}
        self.lock = threading.Lock()
        
        # 从配置创建对象
        try:
            self._create_objects_from_config()
            print("DataObjectManager初始化完成")
        except Exception as e:
            print(f"初始化DataObjectManager时发生错误: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _create_objects_from_config(self) -> None:
        """从配置创建所有数据对象"""
        print("开始从配置创建数据对象...")
        objects_config = self.config_manager.get_objects_config()
        print(f"获取到 {len(objects_config)} 个对象配置")
        
        # 第一步：创建所有非求和类型的对象
        non_sum_objects = {}
        sum_configs = {}
        
        # 将配置分类
        for name, config in objects_config.items():
            data_type = config.get("data_type")
            if data_type == "sum":
                sum_configs[name] = config
            else:
                non_sum_objects[name] = config
        
        print(f"非求和对象数量: {len(non_sum_objects)}, 求和对象数量: {len(sum_configs)}")
        
        # 创建非求和对象
        print("创建非求和对象...")
        with self.lock:
            for name, config in non_sum_objects.items():
                try:
                    print(f"  创建对象 '{name}'，类型: {config.get('data_type')}")
                    generator = create_data_generator(config, name, self)
                    self.objects[name] = generator
                    print(f"  对象 '{name}' 创建成功")
                except Exception as e:
                    print(f"创建数据对象 '{name}' 时出错: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 检查求和对象的依赖关系，按正确顺序创建
        def check_dependencies(sum_name, visited=None, path=None):
            """检查依赖关系，返回应该先创建的对象列表"""
            if visited is None:
                visited = set()
            if path is None:
                path = []
            
            if sum_name in visited:
                print(f"警告: 检测到循环依赖: {' -> '.join(path + [sum_name])}")
                return []
            
            visited.add(sum_name)
            path.append(sum_name)
            
            result = []
            config = sum_configs.get(sum_name)
            if not config:
                return []
                
            sources = config.get("source_objects", [])
            for source in sources:
                if source in sum_configs and source not in self.objects:
                    result.extend(check_dependencies(source, visited.copy(), path.copy()))
            
            if sum_name not in self.objects:
                result.append(sum_name)
            
            return result
        
        # 第二步：创建所有求和类型的对象，确保按依赖顺序创建
        print("分析求和对象依赖关系...")
        creation_order = []
        for name in sum_configs:
            if name not in self.objects:
                deps = check_dependencies(name)
                for dep in deps:
                    if dep not in creation_order:
                        creation_order.append(dep)
        
        print(f"求和对象创建顺序: {creation_order}")
        
        # 按顺序创建求和对象
        print("创建求和对象...")
        sum_generators = []  # 保存创建的求和对象，稍后进行初始化
        
        with self.lock:
            for name in creation_order:
                config = sum_configs.get(name)
                try:
                    print(f"  创建求和对象 '{name}'，源对象: {config.get('source_objects', [])}")
                    generator = create_data_generator(config, name, self)
                    self.objects[name] = generator
                    if isinstance(generator, SumDataGenerator):
                        sum_generators.append(generator)
                    print(f"  求和对象 '{name}' 创建成功")
                except Exception as e:
                    print(f"创建求和对象 '{name}' 时出错: {e}")
                    import traceback
                    traceback.print_exc()
        
        # 第三步：所有对象创建完成后，初始化求和对象
        print("所有对象创建完成，开始初始化求和对象...")
        for generator in sum_generators:
            try:
                print(f"  初始化求和对象 '{generator.name}'")
                generator.first_update()  # 调用first_update方法进行首次数据更新
                print(f"  求和对象 '{generator.name}' 初始化成功")
            except Exception as e:
                print(f"初始化求和对象 '{generator.name}' 时出错: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"所有对象创建完成，总数: {len(self.objects)}")
    
    def start_all(self) -> None:
        """启动所有数据生成器"""
        with self.lock:
            for generator in self.objects.values():
                generator.start()
    
    def stop_all(self) -> None:
        """停止所有数据生成器"""
        with self.lock:
            for generator in self.objects.values():
                generator.stop()
    
    def get_object_names(self) -> List[str]:
        """
        获取所有对象名称
        
        Returns:
            List[str]: 对象名称列表
        """
        with self.lock:
            return list(self.objects.keys())
    
    def get_object(self, name: str) -> Optional[BaseDataGenerator]:
        """
        获取指定对象的生成器
        
        Args:
            name: 对象名称
            
        Returns:
            Optional[BaseDataGenerator]: 数据生成器，如果不存在则返回None
        """
        with self.lock:
            return self.objects.get(name)
    
    def get_all_current_data(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有对象的当前数据
        
        Returns:
            Dict[str, Dict[str, Any]]: 对象名称到数据的映射
        """
        result = {}
        with self.lock:
            for name, generator in self.objects.items():
                result[name] = generator.get_current_data()
        return result
    
    def get_all_object_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有对象的配置
        
        Returns:
            Dict[str, Dict[str, Any]]: 对象名称到配置的映射
        """
        result = {}
        with self.lock:
            for name, generator in self.objects.items():
                result[name] = generator.get_config()
        return result 