# Netcore

[![JOSS Paper](https://joss.theoj.org/papers/08b1c73b184c1341f51e01ee052647ae/status.svg)](https://joss.theoj.org/papers/08b1c73b184c1341f51e01ee052647ae) ![PyPI - Version](https://img.shields.io/pypi/v/netcore?label=PyPI&color=green) ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

[English](README.md) | 简体中文

Netcore 是一个轻量级通信框架，专为**单一连接中的并发消息传输**设计。通过创新的消息分块和调度机制，允许在不建立多个连接的情况下同时处理多路消息流，显著提升资源受限场景下的通信效率。

## 核心特性

### 🚀 并发传输引擎
- **单连接多路复用**：在单一物理连接上实现逻辑并发的消息流
- **智能分块调度**：自动将大消息拆分为块并交错传输，最大化带宽利用率
- **非阻塞 I/O**：消息传输与业务处理解耦，保障系统响应速度

### 📦 协议与传输
- **自适应协议层**：
  - 支持二进制/JSON/原始数据格式
  - 可配置分块大小（默认 4KB）
  - 内存与文件混合存储模式
- **传输抽象接口**：
  - 兼容任意 I/O 设备（串口/TCP/蓝牙等）
  - 提供同步/异步双模式 API
  - 线程安全的消息队列管理

### 🧩 企业级功能
- **蓝图系统**：
  - 模块化路由分组（支持前缀和嵌套）
  - 蓝图级中间件和错误处理
  - 热插拔组件注册机制
- **事件中枢**：
  - 发布-订阅模式
  - 一次性事件绑定
  - 系统生命周期事件监控（启动/关闭/错误）
- **任务调度器**：
  - 毫秒级定时任务
  - 自适应优先级队列
  - 失败任务重试机制
- **智能缓存**：
  - LRU 内存缓存
  - TTL 自动失效
  - 缓存穿透保护
  - 线程安全访问

## 安装

```bash
pip install netcore
```

**系统要求**：
- Python ≥ 3.8
- 无额外依赖（纯标准库实现）

## 快速开始

### 基础示例：串口通信
```python
from netcore import Endpoint, Pipe
import serial

# 初始化串口设备
ser = serial.Serial('/dev/ttyUSB0', 115200)

# 创建通信管道（仅需提供读写函数）
pipe = Pipe(ser.read, ser.write)
endpoint = Endpoint(pipe)

# 注册消息处理器
@endpoint.request('sensor_data')
def handle_sensor():
    return Response('sensor_ack', {"status": "OK"})

# 启动服务（默认启用 4 个工作线程）
endpoint.start()
```

## 架构说明：
1. **应用层 (Endpoint)**  
   - 路由系统：处理消息路由和蓝图注册
   - 事件系统：实现发布-订阅模式的事件中枢
   - 任务系统：管理定时任务和优先级队列
   - 缓存系统：提供线程安全的LRU缓存机制

2. **传输层 (Pipe)**  
   - 发送队列：实现优先级任务队列管理
   - 接收池：维护临时和完整的消息存储
   - 线程锁：确保共享资源的线程安全访问
   - 协议集成：深度依赖LsoProtocol实现分块传输

3. **协议层 (LsoProtocol)**  
   - 智能分块：根据数据类型自动选择内存/文件存储
   - 元数据管理：维护扩展头和消息完整性校验
   - 混合存储：支持内存缓冲与持久化文件的无缝切换

4. **并发模型**  
   - 主线程：负责I/O监听和请求入队
   - 工作线程池：从队列获取请求并独立处理
   - 线程隔离：通过线程本地存储实现请求上下文隔离

5. **数据流**  
   - 双向通道：展示从应用层到物理设备的完整闭环
   - 协议透明：序列化/反序列化过程对上层完全隐藏
   - 异步处理：非阻塞传输与业务逻辑解耦

## 文档与支持

📚 [完整文档](https://netcore.acdp.top) | 💬 [社区讨论](https://github.com/A03HCY/Netcore/discussions) | 🐛 [问题追踪](https://github.com/A03HCY/Netcore/issues)

文档包含：
- API 参考手册
- 架构设计白皮书
- 最佳实践指南
- 性能优化技巧

## 贡献指南

欢迎通过以下方式参与贡献：
1. 提交 Pull Request 改进代码
2. 完善文档或翻译
3. 提交测试用例
4. 报告安全漏洞

## 许可证

[MIT License](LICENSE)