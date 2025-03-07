# 模拟数据生成器服务

这是一个用于生成多种模拟数据的服务系统，支持创建多个独立的数据对象，并通过REST API提供数据访问。系统基于配置文件进行设置，无需编程即可定制各种数据生成行为。

## 核心功能

- **多对象支持**：同时管理多个独立的数据对象
- **可配置的数据生成**：支持随机、步进、订单和求和四种数据生成模式
- **RESTful API**：基于FastAPI的现代化API设计
- **历史数据**：为每个对象保存历史数据记录
- **配置文件驱动**：通过JSON配置文件进行所有设置
- **Docker容器化**：支持Docker容器部署
- **外部配置**：支持将配置文件放在Docker镜像外部，便于修改

## 数据类型介绍

### 1. 随机数据 (random)
生成在指定范围内随机变化的数据值。
- 特有参数：
  - `base_value`：基础值
  - `update_range`：每次更新的变化范围 [最小变化量, 最大变化量]
  - `min_value`/`max_value`：值的上下限

### 2. 步进数据 (step)
按预设值列表按顺序生成数据。
- 特有参数：
  - `values`：值列表，如 [10, 20, 30, 40]
  - `dwell_time`：每个值停留的时间(秒)
  - `loop`：是否循环，为true时循环生成，为false时到达列表末尾后保持最后一个值

### 3. 订单数据 (order)
生成模拟订单数据，包含订单号、时间、地点和算力需求量。
- 特有参数：
  - `order_id_base`：订单号基础值
  - `id_increment_range`：每次订单号增加的范围 [最小增量, 最大增量]
  - `locations`：可选的地点列表
  - `power_demand_range`：算力需求量范围 [最小值, 最大值]
  - `interval_range`：生成新订单的时间间隔范围（秒）[最小间隔, 最大间隔]
  - `history_limit`：保存的历史订单数量，默认为20

### 4. 求和数据 (sum)
计算多个指定数据源的当前值的总和。
- 特有参数：
  - `source_objects`：源数据对象名称列表，如 ["温度传感器", "压力传感器"]
  - `update_interval`：更新间隔（秒），默认为5.0
  - `history_limit`：保存的历史数据点数量
  - `description`：可选的描述信息

## 配置文件说明

系统使用`config.json`文件存储所有配置，结构如下：
```json
{
  "global_settings": {
    "api_port": 8000,
    "api_host": "0.0.0.0"
  },
  "objects": {
    "对象名称1": {
      "data_type": "random或step或order或sum",
      "其他配置参数..."
    },
    "对象名称2": {
      "数据配置..."
    }
  }
}
```

**重要提示**：系统仅在启动时读取配置文件，修改配置后需要重启服务生效。

## API使用指南

系统提供以下主要API接口：

### 基础API
- `GET /`：获取服务基本信息
- `GET /api/objects`：获取所有数据对象列表

### 数据API
- `GET /api/data/{object_name}`：获取指定对象的当前数据
- `GET /api/data`：获取所有对象的当前数据
- `GET /api/data/{object_name}/history?count={count}`：获取指定对象的历史数据，可选参数count指定获取数量
- `GET /api/orders/{object_name}?count={count}`：获取指定订单对象的订单数据，可选参数count指定获取数量（默认10条）
- `GET /api/sum/{object_name}/sources`：获取指定求和对象的所有源数据

### 配置API（只读）
- `GET /api/config/global`：获取全局配置
- `GET /api/config/{object_name}`：获取指定对象的配置
- `GET /api/config`：获取所有对象的配置

## 快速入门

### 使用Docker（推荐）

1. 克隆本仓库或下载源代码：
   ```bash
   git clone https://github.com/your-username/data-simulator.git
   cd data-simulator
   ```

2. 创建配置目录并准备配置文件：
   ```bash
   mkdir -p config
   cp config.json config/
   ```

3. 根据需要编辑`config/config.json`配置文件，定制数据对象。

4. 使用Docker Compose构建并启动服务：
   ```bash
   docker-compose up -d
   ```

5. 访问API：
   - API文档：http://localhost:8000/docs
   - 基本信息：http://localhost:8000/

### 配置文件挂载

Docker容器会从`/config/config.json`路径读取配置文件。通过Docker Compose，我们将本地的`./config`目录挂载到容器的`/config`目录，这样您可以在不重新构建镜像的情况下修改配置。

修改配置后，只需重启容器即可应用新配置：
```bash
docker-compose restart
```

### 手动安装

1. 确保安装了Python 3.8或以上版本。

2. 克隆本仓库或下载源代码：
   ```bash
   git clone https://github.com/your-username/data-simulator.git
   cd data-simulator
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 编辑`config.json`配置文件，根据需要定制数据对象。

5. 运行服务：
   ```bash
   python main.py
   ```

6. 访问API：
   - API文档：http://localhost:8000/docs
   - 基本信息：http://localhost:8000/

## 最佳实践

1. **合理设置更新频率**：根据实际需求设置合适的更新频率，避免过于频繁的更新
2. **合理使用循环设置**：步进数据的`loop`属性可控制是否循环生成数据
3. **配置文件管理**：修改配置后需重启服务，建议保留配置文件备份
4. **历史数据限制**：系统默认只保留最近200个数据点，请适时获取历史数据
5. **容器化管理**：使用Docker可以方便地管理服务，并确保环境一致性
6. **外部配置**：将配置文件放在Docker镜像外部，便于修改和管理
7. **订单数据获取**：使用专用的订单API接口获取订单数据，可以指定获取的数量
8. **求和数据配置**：为求和数据类型指定正确的源数据对象，确保源对象先于求和对象定义

## 开发与扩展

如需扩展系统功能，可以关注以下几个核心类：
- `ConfigManager`：负责配置管理
- `DataGenerator`：负责数据生成
- `DataObjectManager`：负责管理多个数据对象
- `api_server.py`：API接口实现

## 许可证

MIT 