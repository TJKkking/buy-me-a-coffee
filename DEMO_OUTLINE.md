# Buy A Coffee -- 多门店 Session State Demo 文档大纲

## 1. Demo 概述
- 一句话说明：基于 Google ADK 的多 Agent 系统，展示多门店场景下 Session State 在 Agent 间的可靠传递
- 核心特性清单（3-4 条）
- 技术栈速览表

## 2. 架构总览
- 系统架构图（mermaid，展示前端 → Gateway → Root Agent → 子 Agent → API → DB 的分层关系）
- 两种部署模式对比：统一部署 vs 分布式部署（表格：进程数、通信方式、state 传递机制）

## 3. 多门店设计
- 数据模型：stores 表 + store_product_availability 表 + orders.store_id
- 门店种子数据（3 家门店）
- 前端门店选择器交互说明
- store_id 全链路穿透图（mermaid sequence diagram）：
  Frontend X-Store-Id Header → Gateway → Session State → ToolContext → HTTP Header → API → SQL WHERE

## 4. Session State 参数传递（核心亮点）

### 4.1 统一部署模式
- Gateway 创建 session 时写入门店信息
- 所有子 Agent 共享同一 Runner/SessionService
- 工具函数通过 ToolContext.state["store_id"] 读取（代码片段）
- 动态 Instruction：_dynamic_instruction 从 state 注入门店上下文

### 4.2 分布式部署模式（A2A）
- 问题：远程 Agent 有独立的 SessionService，session state 无法跨进程共享
- 解决方案架构图（mermaid sequence diagram）：
  Gateway _store_meta_provider → SendMessageRequest.metadata → StoreAwareA2aExecutor._prepare_session → remote session.state
- 三个关键组件说明：
  - a2a_request_meta_provider（ADK 官方 API）
  - SendMessageRequest.metadata（A2A 协议标准字段）
  - StoreAwareA2aExecutor（自定义 Executor 桥接 metadata → state）
- 设计要点：远程工具代码与统一模式零差异

### 4.3 Session State 调试日志
- 日志格式示例（初始状态 / 状态变更 / 结束状态）

## 5. 快速开始
- 环境准备（Python、Node.js、API Key）
- 一键启动：make dev
- 访问地址
- 基本操作流程（选门店 → 点咖啡 → 查订单 → 叫配送）

## 6. 后续扩展
- 替换为持久化 SessionService（当前 InMemorySessionService 的替换点）
- 管理端 Agent（底层已预留：stores.status、store_product_availability、stats API）
- 生产部署注意事项
