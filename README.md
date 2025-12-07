
> 注：当前项目为 Serverless Devs 应用，由于应用中会存在需要初始化才可运行的变量（例如应用部署地区、函数名等等），所以**不推荐**直接 Clone 本仓库到本地进行部署或直接复制 s.yaml 使用，**强烈推荐**通过 `s init ${模版名称}` 的方法或应用中心进行初始化，详情可参考[部署 & 体验](#部署--体验) 。

# buy-me-a-coffee 帮助文档
<p align="center" class="flex justify-center">
    <a href="https://www.serverless-devs.com" class="ml-1">
    <img src="http://editor.devsapp.cn/icon?package=buy-me-a-coffee&type=packageType">
  </a>
  <a href="http://www.devsapp.cn/details.html?name=buy-me-a-coffee" class="ml-1">
    <img src="http://editor.devsapp.cn/icon?package=buy-me-a-coffee&type=packageVersion">
  </a>
  <a href="http://www.devsapp.cn/details.html?name=buy-me-a-coffee" class="ml-1">
    <img src="http://editor.devsapp.cn/icon?package=buy-me-a-coffee&type=packageDownload">
  </a>
</p>

<description>

希希咖啡店——AgentRun A2A 协议多 Agent 案例

</description>

<codeUrl>



</codeUrl>
<preview>



</preview>


## 前期准备

使用该项目，您需要有开通以下服务：

<service>
</service>

推荐您拥有以下的产品权限 / 策略：
<auth>



| 服务/业务 |  权限 |  备注  |
| --- |  --- |   --- |
| 函数计算 | AliyunFCFullAccess |   |
| AgentRun | AliyunAgentRunFullAccess |   |
| FunctionAI | AliyunDevsReadOnlyAccess |   |

</auth>

<remark>



</remark>

<disclaimers>



</disclaimers>

## 部署 & 体验

<appcenter>
   
- :fire: 通过 [Serverless 应用中心](https://fcnext.console.aliyun.com/applications/create?template=buy-me-a-coffee) ，
  [![Deploy with Severless Devs](https://img.alicdn.com/imgextra/i1/O1CN01w5RFbX1v45s8TIXPz_!!6000000006118-55-tps-95-28.svg)](https://fcnext.console.aliyun.com/applications/create?template=buy-me-a-coffee) 该应用。
   
</appcenter>
<deploy>
    
- 通过 [Serverless Devs Cli](https://www.serverless-devs.com/serverless-devs/install) 进行部署：
  - [安装 Serverless Devs Cli 开发者工具](https://www.serverless-devs.com/serverless-devs/install) ，并进行[授权信息配置](https://docs.serverless-devs.com/fc/config) ；
  - 初始化项目：`s init buy-me-a-coffee -d buy-me-a-coffee`
  - 进入项目，并进行项目部署：`cd buy-me-a-coffee && s deploy -y`
   
</deploy>

## 应用详情

<appdetail id="flushContent">

### 希希咖啡店 - 多 Agent 协同模板

#### 模板概述

**希希咖啡店**是基于 Google ADK 框架构建的 A2A（Agent-to-Agent）协议多 Agent 协同案例模板。该模板展示了如何通过标准化的 A2A 协议，让通用智能体（寒小艾）与业务领域 Agent（希希咖啡店、送了么配送）实现无缝协同，并将业务后端服务通过 OpenAPI 快速集成。

**适用场景：**
- 多业务系统 Agent 协同
- 通用 AI 助手能力扩展
- 企业级服务集成
- 云原生 Agent 应用

**核心功能：**
- A2A 协议 Agent 通信
- OpenAPI 业务接口集成
- 云原生弹性部署

#### 技术架构

**使用框架：** Google ADK（Agent Development Kit）

**架构组件：**

| 组件 | 部署方式 | 说明 |
|------|---------|------|
| 前端 | 函数计算（自定义运行时） | 用户交互界面 |
| 寒小艾（主 Agent） | AgentRun 镜像部署 | 核心协调者，通用智能体 |
| 希希咖啡店 Agent | AgentRun 镜像部署 | 咖啡点单业务 Agent |
| 希希咖啡店后端 | 函数计算镜像部署 | 咖啡店业务逻辑，OpenAPI 接口 |
| 送了么 Agent | AgentRun 镜像部署 | 配送业务 Agent |
| 送了么后端 | 函数计算镜像部署 | 配送业务逻辑，OpenAPI 接口 |

**技术要求：**
- 支持 A2A 协议的 Agent 通信
- 后端服务提供 OpenAPI 规范接口
- 支持自定义大语言模型选择

### 功能说明

#### 主要功能模块

1. **通用对话**：寒小艾提供基础 AI 对话能力
2. **咖啡点单**：调用希希咖啡店 Agent，通过 OpenAPI 访问后端服务
3. **配送服务**：调用送了么 Agent，通过 OpenAPI 访问配送系统
4. **全流程协同**：支持"咨询 → 下单 → 配送"完整业务链路

#### Agent 能力

- **服务发现**：通过 A2A 协议连接业务 Agent
- **工具调用**：通过 FunctionAI Toolset 集成后端 OpenAPI 服务
- **能力组合**：灵活组合多个 Agent 和后端服务


### 使用示例

#### 应用场景示例

**场景一：咖啡咨询**
```
用户："你们有什么咖啡？"
寒小艾 → 希希咖啡店 Agent → 希希咖啡店后端（查询菜单）
返回："我们有美式、拿铁、卡布奇诺..."
```

**场景二：完整下单流程**
```
用户："帮我点一杯大杯拿铁，配送到中关村大厦"
寒小艾 → 希希咖啡店 Agent → 后端（创建订单）
      → 送了么 Agent → 后端（创建配送单）
返回："订单已确认，预计 30 分钟送达，配送费 5 元"
```



</appdetail>

## 使用文档

<usedetail id="flushContent">
</usedetail>


<devgroup>


## 开发者社区

您如果有关于错误的反馈或者未来的期待，您可以在 [Serverless Devs repo Issues](https://github.com/serverless-devs/serverless-devs/issues) 中进行反馈和交流。如果您想要加入我们的讨论组或者了解 FC 组件的最新动态，您可以通过以下渠道进行：

<p align="center">  

| <img src="https://serverless-article-picture.oss-cn-hangzhou.aliyuncs.com/1635407298906_20211028074819117230.png" width="130px" > | <img src="https://serverless-article-picture.oss-cn-hangzhou.aliyuncs.com/1635407044136_20211028074404326599.png" width="130px" > | <img src="https://serverless-article-picture.oss-cn-hangzhou.aliyuncs.com/1635407252200_20211028074732517533.png" width="130px" > |
| --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| <center>微信公众号：`serverless`</center>                                                                                         | <center>微信小助手：`xiaojiangwh`</center>                                                                                        | <center>钉钉交流群：`33947367`</center>                                                                                           |
</p>
</devgroup>
