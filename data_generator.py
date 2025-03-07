import random
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import threading


class DataPoint:
    """数据点类，表示一个时间点的数据"""
    
    def __init__(self, value: float, timestamp: Optional[datetime] = None):
        """
        初始化数据点
        
        Args:
            value: 数据值
            timestamp: 时间戳，默认为当前时间
        """
        self.value = value
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat()
        }


class BaseDataGenerator:
    """基础数据生成器类"""
    
    def __init__(self, config: Dict[str, Any], name: str, auto_update: bool = True):
        """
        初始化基础数据生成器
        
        Args:
            config: 配置字典
            name: 数据对象名称
            auto_update: 是否在初始化时自动更新，默认为True
        """

        self.config = config
        self.name = name
        self.history: List[DataPoint] = []
        self.history_limit = config.get("history_limit", 200)
        self.current_value = 0.0


        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        
        # 生成初始值 - 但只在明确请求时才执行
        if auto_update:
            self.update()
    
    def start(self) -> None:
        """启动数据生成器"""
        self.running = True
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self) -> None:
        """停止数据生成器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def _update_loop(self) -> None:
        """更新循环"""
        update_interval = self.config.get("update_interval", 1.0)
        while self.running:
            self.update()
            time.sleep(update_interval)
    
    def update(self) -> None:
        """更新数据值，子类必须实现此方法"""
        raise NotImplementedError("子类必须实现update方法")
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        获取当前数据
        
        Returns:
            Dict[str, Any]: 当前数据字典
        """
        with self.lock:
            if not self.history:
                return {"name": self.name, "value": None, "timestamp": None}
            
            latest = self.history[-1]
            return {
                "name": self.name,
                "value": latest.value,
                "timestamp": latest.timestamp.isoformat()
            }
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        获取历史数据
        
        Returns:
            List[Dict[str, Any]]: 历史数据列表
        """
        with self.lock:
            return [point.to_dict() for point in self.history]
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取配置
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.config


class RandomDataGenerator(BaseDataGenerator):
    """随机数据生成器类"""
    
    def __init__(self, config: Dict[str, Any], name: str):
        """
        初始化随机数据生成器
        
        Args:
            config: 配置字典
            name: 数据对象名称
        """
    
        self.base_value = config.get("base_value", 0.0)

        self.update_range = config.get("update_range", [-1.0, 1.0])

        self.min_value = config.get("min_value", float('-inf'))

        self.max_value = config.get("max_value", float('inf'))

        # 调用父类构造函数
        super().__init__(config, name, True)
    
    def update(self) -> None:
        """生成随机数据"""
        # 生成随机变化量
        change = random.uniform(self.update_range[0], self.update_range[1])

        # 先计算新值，不需要锁
        with self.lock:
            current_value = self.current_value if self.history else self.base_value

        
        new_value = current_value + change
        
        # 限制在最大最小值范围内
        new_value = max(self.min_value, min(self.max_value, new_value))
        
        # 直接更新内部状态，而不是调用可能再次获取锁的方法
        with self.lock:
            self.current_value = new_value
            data_point = DataPoint(new_value)#
            self.history.append(data_point)
            
            # 限制历史记录长度
            if len(self.history) > self.history_limit:
                self.history = self.history[-self.history_limit:]


class StepDataGenerator(BaseDataGenerator):
    """步进数据生成器类"""
    
    def __init__(self, config: Dict[str, Any], name: str):
        """
        初始化步进数据生成器
        
        Args:
            config: 配置字典
            name: 数据对象名称
        """
        self.values = config.get("values", [0.0])
        self.dwell_time = config.get("dwell_time", 1.0)
        self.loop = config.get("loop", True)
        self.current_index = 0
        self.last_change_time = time.time()
        
        # 调用父类构造函数
        super().__init__(config, name, True)
    
    def update(self) -> None:
        """生成步进数据"""
        # 如果值列表为空，则不更新
        if not self.values:
            return
        
        current_time = time.time()
        
        # 检查是否应该切换到下一个值
        if current_time - self.last_change_time >= self.dwell_time:
            self.last_change_time = current_time
            
            # 更新索引
            if self.current_index < len(self.values) - 1:
                self.current_index += 1
            elif self.loop:
                # 循环到开始
                self.current_index = 0
            # 如果不循环且已经到末尾，则保持当前值
        
        # 获取当前值
        current_value = self.values[self.current_index]
        
        # 检查是否需要更新历史记录
        with self.lock:
            if not self.history or self.history[-1].value != current_value:
                # 直接更新，不调用可能获取锁的方法
                self.current_value = current_value
                data_point = DataPoint(current_value)
                self.history.append(data_point)
                
                # 限制历史记录长度
                if len(self.history) > self.history_limit:
                    self.history = self.history[-self.history_limit:]


class OrderDataGenerator(BaseDataGenerator):
    """订单数据生成器类"""
    
    def __init__(self, config: Dict[str, Any], name: str):
        """
        初始化订单数据生成器
        
        Args:
            config: 配置字典
            name: 数据对象名称
        """
        # 设置默认的历史记录限制为20条订单
        if "history_limit" not in config:
            config["history_limit"] = 20
        
        # 订单特有属性
        self.order_id_base = config.get("order_id_base", 1000000000)
        self.current_order_id = self.order_id_base
        self.id_increment_range = config.get("id_increment_range", [1, 10])
        self.locations = config.get("locations", ["北京", "上海", "深圳", "成都"])
        self.power_demand_range = config.get("power_demand_range", [100, 1000])
        # 读取数据单位配置
        self.unit = config.get("unit", "")
        
        # 生成订单的时间间隔随机范围（秒）
        self.interval_range = config.get("interval_range", [5, 30])
        self.next_update_time = time.time()
            
        # 调用父类构造函数
        super().__init__(config, name, True)
    
    def _update_loop(self) -> None:
        """重写更新循环，使用随机时间间隔"""
        while self.running:
            current_time = time.time()
            
            # 检查是否应该生成新订单
            if current_time >= self.next_update_time:
                self.update()
                
                # 设置下一次更新的时间
                interval = random.uniform(self.interval_range[0], self.interval_range[1])
                self.next_update_time = current_time + interval
            
            # 小睡一会，避免CPU占用过高
            time.sleep(0.1)
    
    def update(self) -> None:
        """生成新订单数据"""
        with self.lock:
            # 增加订单ID
            id_increment = random.randint(self.id_increment_range[0], self.id_increment_range[1])
            self.current_order_id += id_increment
            
            # 生成订单数据
            order_data = {
                "order_id": self.current_order_id,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "location": random.choice(self.locations),
                "power_demand": random.randint(self.power_demand_range[0], self.power_demand_range[1])
                # 不再包含独立的unit字段，因为在get方法中会将其与数值组合
            }
            
            # 直接更新历史记录，不调用可能获取锁的方法
            data_point = DataPoint(order_data)
            self.history.append(data_point)
            
            # 限制历史记录长度
            if len(self.history) > self.history_limit:
                self.history = self.history[-self.history_limit:]
    
    def get_current_data(self) -> Dict[str, Any]:
        """
        获取当前订单数据
        
        Returns:
            Dict[str, Any]: 当前订单数据
        """
        with self.lock:
            if not self.history:
                return {"name": self.name, "value": None, "timestamp": None}
            
            latest = self.history[-1]
            latest_value = latest.value.copy() if isinstance(latest.value, dict) else {}
            
            # 将power_demand数值与单位格式化为"数值 (单位)"
            if isinstance(latest.value, dict) and "power_demand" in latest.value and self.unit:
                power_demand = latest.value["power_demand"]
                latest_value["power_demand"] = f"{power_demand} ({self.unit})"
            
            result = {
                "name": self.name,
                "value": latest_value,
                "timestamp": latest.timestamp.isoformat()
            }
            
            return result
    
    def get_history(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取历史订单数据
        
        Args:
            count: 要获取的订单数量，如果为None则获取全部
            
        Returns:
            List[Dict[str, Any]]: 历史订单数据列表
        """
        with self.lock:
            history_data = []
            
            if count is None or count >= len(self.history):
                history_points = self.history
            else:
                history_points = self.history[-count:]
                
            for point in history_points:
                data = point.to_dict()
                value_dict = data["value"].copy() if isinstance(data["value"], dict) else {}
                
                # 将power_demand数值与单位格式化为"数值 (单位)"
                if isinstance(data["value"], dict) and "power_demand" in data["value"] and self.unit:
                    power_demand = data["value"]["power_demand"]
                    value_dict["power_demand"] = f"{power_demand} ({self.unit})"
                
                # 更新格式化后的值
                data["value"] = value_dict
                history_data.append(data)
                
            return history_data


class SumDataGenerator:
    """数据求和生成器类，计算多个指定数据源的和"""
    
    def __init__(self, config, name, object_manager=None):
        """
        初始化数据求和生成器
        """
        # 存储基本属性但不执行任何计算
        self.config = config
        self.name = name
        self.object_manager = object_manager
        self.source_objects = config.get("source_objects", [])
        self.history = []
        self.history_limit = config.get("history_limit", 200)
        self.current_value = 0.0
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
    
    def first_update(self):
        """首次更新，计算并存储初始值"""
        self.update()
    
    def update(self):
        """计算和更新求和值"""
        if not self.object_manager or not self.source_objects:
            return

        total = 0.0
        count = 0
        
        try:
            for name in self.source_objects:
                try:
                    obj = self.object_manager.get_object(name)
                    if obj:
                        data = obj.get_current_data()
                        if data and data.get("value") is not None:
                            value = data.get("value")
                            if isinstance(value, (int, float)):
                                total += value
                                count += 1
                except Exception as e:
                    print(f"处理源对象 '{name}' 时出错: {str(e)}")
                    # 继续处理其他源对象，不要让一个对象的失败影响整个计算
            
            if count > 0:
                # 直接更新历史记录，不调用_add_to_history方法
                with self.lock:
                    self.current_value = total
                    data_point = DataPoint(total)
                    self.history.append(data_point)
                    
                    if len(self.history) > self.history_limit:
                        self.history = self.history[-self.history_limit:]
        except Exception as e:
            print(f"求和对象 '{self.name}' 更新时发生错误: {str(e)}")
            # 不抛出异常，以免中断更新循环
    
    def start(self):
        """启动生成器"""
        self.running = True
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """停止生成器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def _update_loop(self):
        """更新循环"""
        update_interval = self.config.get("update_interval", 5.0)
        while self.running:
            self.update()
            time.sleep(update_interval)
    
    def get_current_data(self):
        """获取当前数据"""
        with self.lock:
            if not self.history:
                return {"name": self.name, "value": None, "timestamp": None}
            
            latest = self.history[-1]
            return {
                "name": self.name,
                "value": latest.value,
                "timestamp": latest.timestamp.isoformat()
            }
    
    def get_history(self):
        """获取历史数据"""
        with self.lock:
            return [point.to_dict() for point in self.history]
    
    def get_config(self):
        """获取配置"""
        return self.config
    
    def get_source_data(self):
        """获取源数据"""
        result = {}
        if not self.object_manager:
            return result
            
        for name in self.source_objects:
            obj = self.object_manager.get_object(name)
            if obj:
                result[name] = obj.get_current_data()
        
        return result


def create_data_generator(config: Dict[str, Any], name: str, object_manager=None) -> BaseDataGenerator:
    """
    根据配置创建数据生成器
    
    Args:
        config: 配置字典
        name: 数据对象名称
        object_manager: 数据对象管理器实例，用于创建SumDataGenerator
        
    Returns:
        BaseDataGenerator: 数据生成器实例
    
    Raises:
        ValueError: 如果数据类型不受支持
    """
    data_type = config.get("data_type")
    
    if data_type == "random":
        return RandomDataGenerator(config, name)
    elif data_type == "step":
        return StepDataGenerator(config, name)
    elif data_type == "order":
        return OrderDataGenerator(config, name)
    elif data_type == "sum":
        # 创建求和生成器，确保传入对象管理器并避免自动更新
        if object_manager is None:
            print(f"警告: 创建求和数据对象 '{name}' 时未提供对象管理器实例")
        return SumDataGenerator(config, name, object_manager)
    else:
        raise ValueError(f"不支持的数据类型: {data_type}") 