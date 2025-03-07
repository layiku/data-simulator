import time
import json
from config_manager import ConfigManager
from data_object_manager import DataObjectManager
import requests

def test_local_order_generator():
    """直接测试OrderDataGenerator的单位格式化功能"""
    print("=== 开始测试订单数据单位格式化功能 ===")
    
    # 初始化配置管理器
    config_manager = ConfigManager("config.json")
    
    # 初始化数据对象管理器
    object_manager = DataObjectManager(config_manager)
    
    # 获取订单对象
    order_generator = object_manager.get_object("算力订单")
    
    if not order_generator:
        print("错误：未找到算力订单对象")
        return
    
    # 获取并显示当前订单数据
    current_data = order_generator.get_current_data()
    print("\n当前数据:")
    print(json.dumps(current_data, indent=2, ensure_ascii=False))
    
    # 生成几个新订单
    print("\n生成3个新订单...")
    for i in range(3):
        order_generator.update()
        time.sleep(0.5)
    
    # 获取并显示历史订单数据
    history_data = order_generator.get_history(5)
    print("\n历史数据:")
    print(json.dumps(history_data, indent=2, ensure_ascii=False))
    
    print("\n=== 测试完成 ===")

def test_api_order():
    """通过API测试订单数据单位格式化功能"""
    print("=== 开始测试API订单数据单位格式化 ===")
    
    try:
        # 检查API服务是否运行
        base_url = "http://localhost:8000"
        print(f"测试API连接: {base_url}")
        
        response = requests.get(f"{base_url}/api/objects")
        if response.status_code != 200:
            print(f"错误: API服务未响应，状态码: {response.status_code}")
            return
        
        objects = response.json()
        print(f"可用对象: {objects}")
        
        if "算力订单" in objects:
            # 获取当前订单数据
            response = requests.get(f"{base_url}/api/data/算力订单")
            if response.status_code == 200:
                data = response.json()
                print("\nAPI当前订单数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 获取历史订单数据
            response = requests.get(f"{base_url}/api/data/算力订单/history?count=5")
            if response.status_code == 200:
                history = response.json()
                print("\nAPI历史订单数据:")
                print(json.dumps(history, indent=2, ensure_ascii=False))
        else:
            print("错误: 未找到算力订单对象")
    
    except Exception as e:
        print(f"测试API时出错: {str(e)}")
    
    print("\n=== API测试完成 ===")

if __name__ == "__main__":
    # 先测试本地对象
    test_local_order_generator()
    
    # 测试API接口
    test_api_order() 