# ☕ Buy A Coffee - 多 Agent 咖啡订购系统

<p align="center">
  <img src="docs/architecture.svg" alt="系统架构图" width="100%">
</p>

基于 **Google ADK** 的多 Agent 系统，使用 **Python** 作为后端，**CopilotKit** + **AG-UI** 作为前端，实现智能咖啡订购和配送服务。

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4?style=flat-square&logo=google)](https://google.github.io/adk-docs/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 🌟 功能特性

### 🤖 多 Agent 协作系统

<p align="center">
  <img src="docs/agent-flow.svg" alt="Agent 交互流程" width="80%">
</p>

| Agent | 功能 | 描述 |
|:------|:-----|:-----|
| 🎯 **Root Agent** | 系统入口 | 意图识别、智能路由到子 Agent |
| 🌤️ **助手 Agent** | 日常助手 | 天气查询、时间管理、提醒设置 |
| ☕ **咖啡 Agent** | 咖啡服务 | 管理下单和查询子 Agent |
| 📝 **下单 Agent** | 点单服务 | 展示菜单、创建订单 |
| 🔍 **查询 Agent** | 订单查询 | 查询订单状态和历史 |
| 🛵 **配送 Agent** | 配送服务 | 安排配送、查询配送状态 |

### 🎯 核心能力展示

| 能力 | 说明 |
|:-----|:-----|
| **A2A (Agent-to-Agent)** | 6 个 Agent 协同工作，智能路由分发任务 |
| **Tool Calling** | 丰富的工具集成：天气、时间、订单、配送 |
| **Multi-System** | 咖啡店系统与配送系统无缝协同 |
| **Streaming** | SSE 实时流式输出，提升用户体验 |
| **Auto-Init** | 数据库自动创建表和初始化商品数据 |
| **模块化架构** | 各服务可独立部署或统一部署 |

---

## 📁 项目结构

```
buy-a-coffee/
├── 📂 backend/
│   ├── main.py                    # 🚀 主入口（统一部署）
│   ├── config.py                  # ⚙️ 全局配置
│   ├── run_all.py                 # 🎯 启动脚本
│   │
│   ├── 📂 shared/                 # 🔗 共享模块
│   │   └── database.py            #    共享数据库基础设施
│   │
│   ├── 📂 assistant/              # 🌤️ 助手服务
│   │   ├── agent.py               #    Assistant Agent
│   │   └── tools.py               #    天气、时间工具
│   │
│   ├── 📂 coffee/                 # ☕ 希希咖啡服务
│   │   ├── main.py                #    独立部署入口
│   │   ├── agent.py               #    Coffee Agent（含子 Agent）
│   │   ├── api.py                 #    REST API
│   │   ├── database.py            #    咖啡店数据库
│   │   └── tools.py               #    咖啡相关工具
│   │
│   ├── 📂 delivery/               # 🛵 送了么配送服务
│   │   ├── main.py                #    独立部署入口
│   │   ├── agent.py               #    Delivery Agent
│   │   ├── api.py                 #    REST API
│   │   ├── database.py            #    配送数据库
│   │   └── tools.py               #    配送相关工具
│   │
│   └── 📂 gateway/                # 🌐 网关服务
│       ├── main.py                #    统一入口
│       └── agent.py               #    Root Agent
│
├── 📂 frontend/
│   └── 📂 src/
│       ├── 📂 components/         # 🎨 React 组件
│       │   ├── ChatPanel.tsx      #    聊天面板
│       │   ├── OrderPanel.tsx     #    订单管理
│       │   ├── MenuPanel.tsx      #    菜单展示
│       │   └── Header.tsx         #    顶部导航
│       └── App.tsx
│
├── 📂 docs/                       # 📚 文档和图表
├── AGENTS.md                      # 🤖 AI 理解指南
└── README.md
```

---

## 🚀 快速开始

### 环境要求

- **Python** 3.11+
- **Node.js** 18+
- **Google AI API Key** ([获取](https://makersuite.google.com/app/apikey))

### 1️⃣ 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 Google API Key：

```env
GOOGLE_API_KEY=your_api_key_here
```

### 2️⃣ 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务（统一部署）
python main.py
```

🟢 后端将在 **http://localhost:8000** 启动

### 3️⃣ 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

🟢 前端将在 **http://localhost:5173** 启动

---

## 🔄 部署模式

### 统一部署（默认）

所有服务在同一进程中运行，适合开发和小规模部署：

```bash
cd backend
python main.py
# 或
python run_all.py unified
```

### 分离部署

各服务独立运行，适合生产环境和微服务架构：

```bash
# 方式一：使用启动脚本
python run_all.py separate

# 方式二：分别启动各服务
python -m coffee.main      # ☕ 咖啡服务 - 端口 8001
python -m delivery.main    # 🛵 配送服务 - 端口 8002
python -m gateway.main     # 🌐 网关服务 - 端口 8000
```

### 服务端口

| 服务 | 端口 | 描述 |
|:-----|:-----|:-----|
| 🌐 网关 | 8000 | 主入口，整合所有服务 |
| ☕ 咖啡 | 8001 | 希希咖啡独立服务 |
| 🛵 配送 | 8002 | 送了么配送独立服务 |
| 🎨 前端 | 5173 | React 开发服务器 |

---

## 💬 使用示例

### 对话演示

```
👤 用户: 你好

🤖 助手: 你好！👋 欢迎来到希希咖啡！
         我可以帮你：
         ☕ 点咖啡 - 查看菜单、下单
         📋 查订单 - 查询订单状态
         🛵 叫配送 - 安排外卖配送
         🌤️ 查天气 - 了解今日天气

👤 用户: 我想看看菜单

🤖 助手: 这是希希咖啡的菜单 ☕
         
         【经典咖啡】
         ☕ 美式咖啡 - ¥18
         🥛 拿铁咖啡 - ¥22
         ☕ 卡布奇诺 - ¥24
         🍫 摩卡咖啡 - ¥26
         
         【特调饮品】
         🍋 冰摇柠檬茶 - ¥16
         🥭 芒果冰沙 - ¥20
         🍵 抹茶拿铁 - ¥24
         
         请问您想点什么？

👤 用户: 我要一杯拿铁，我叫张三，电话 13800138000

🤖 助手: 好的！已为您创建订单 ✅
         
         📋 订单号：#1
         ☕ 商品：拿铁咖啡 x1
         💰 总计：¥22
         📍 状态：待制作
         
         请问需要配送吗？

👤 用户: 帮我配送到中关村大街1号

🤖 助手: 配送已安排！🛵
         
         🚚 配送单号：#1
         👨‍✈️ 骑手：李师傅 (138****5678)
         ⏱️ 预计 25 分钟送达
         📍 配送地址：中关村大街1号
```

---

## 🔌 API 接口

### 聊天 API

| 端点 | 方法 | 描述 |
|:-----|:-----|:-----|
| `/api/chat` | POST | 非流式聊天 |
| `/api/chat/stream` | POST | SSE 流式聊天 |
| `/api/copilotkit` | POST | CopilotKit 兼容 |

### 咖啡店 API

| 端点 | 方法 | 描述 |
|:-----|:-----|:-----|
| `/api/coffee/products` | GET | 获取商品列表 |
| `/api/coffee/products/{id}` | GET | 获取商品详情 |
| `/api/coffee/orders` | POST | 创建订单 |
| `/api/coffee/orders` | GET | 获取订单列表 |
| `/api/coffee/orders/{id}` | GET | 获取订单详情 |
| `/api/coffee/orders/{id}/status` | PUT | 更新订单状态 |

### 配送 API

| 端点 | 方法 | 描述 |
|:-----|:-----|:-----|
| `/api/delivery/deliveries` | POST | 创建配送 |
| `/api/delivery/deliveries/{id}` | GET | 获取配送详情 |
| `/api/delivery/deliveries/order/{order_id}` | GET | 按订单查配送 |
| `/api/delivery/deliveries/{id}/status` | PUT | 更新配送状态 |

📚 完整 API 文档: **http://localhost:8000/docs**

---

## 🛠️ 技术栈

### 后端

| 技术 | 用途 |
|:-----|:-----|
| **Python 3.11+** | 主要开发语言 |
| **Google ADK** | Agent 开发框架 |
| **FastAPI** | Web 框架 |
| **SQLite** | 数据库 |
| **SSE** | 流式响应 |

### 前端

| 技术 | 用途 |
|:-----|:-----|
| **React 18** | UI 框架 |
| **TypeScript** | 类型安全 |
| **CopilotKit** | AI 聊天组件 |
| **TailwindCSS** | 样式框架 |
| **Vite** | 构建工具 |

---

## 📖 更多文档

- 📄 **[AGENTS.md](AGENTS.md)** - AI 助手项目理解指南（帮助大模型理解项目）
- 🎨 **[docs/architecture.svg](docs/architecture.svg)** - 系统架构图
- 🔄 **[docs/agent-flow.svg](docs/agent-flow.svg)** - Agent 交互流程图

---

## 🎨 界面预览

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ☕ Buy A Coffee - 希希咖啡 · 智能点单助手              🟢 AI 助手在线   │
├────────────────────────────────────────────┬─────────────────────────────┤
│                                            │  📋 订单管理  │  ☕ 菜单    │
│  🤖 你好！欢迎来到希希咖啡！               ├─────────────────────────────┤
│     我可以帮你点咖啡、查订单...            │                             │
│                                            │  #1 待制作      ¥22         │
│  👤 我想点杯拿铁                           │  拿铁咖啡 x1                 │
│                                            │  张三 138****0000            │
│  🤖 好的！请问您贵姓？电话多少？           │                             │
│                                            │  #2 配送中      ¥36         │
│  👤 我叫张三，电话 13800138000             │  美式 x2                     │
│                                            │  🛵 李师傅 25分钟            │
│  🤖 订单创建成功！订单号 #1                │                             │
│     拿铁咖啡 x1，总计 ¥22                  │─────────────────────────────│
│                                            │  待制作: 1  制作中: 0        │
│  ┌─────────────────────────────────────┐  │  已完成: 1                   │
│  │ 输入消息...                    发送 │  │                             │
│  └─────────────────────────────────────┘  │                             │
└────────────────────────────────────────────┴─────────────────────────────┘
```

---

## 📝 注意事项

- 🔑 首次运行需要配置 `GOOGLE_API_KEY`
- 💾 数据库会自动创建和初始化
- 🌤️ 天气数据为模拟数据（实际项目请接入真实 API）
- 🛵 骑手分配为随机模拟（实际项目需要调度系统）
- 🔄 支持统一部署和分离部署两种模式

---

## 📄 许可证

MIT License © 2024

---

<p align="center">
  <b>Buy A Coffee</b> - 用 AI 点一杯咖啡 ☕
  <br>
  <sub>展示 A2A 能力 · 工具调用 · 多系统协同 · 模块化架构</sub>
</p>
