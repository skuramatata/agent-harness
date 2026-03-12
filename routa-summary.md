# Routa - 项目调研总结

## 概述

**Routa** 是一个多智能体协作平台，用于 AI 开发任务的编排与协调。

> GitHub: https://github.com/phodal/routa

## 核心定位

通过专业化角色分工，让多个 AI Agent 协同工作：
- 一个负责规划
- 一个负责实现
- 一个负责验证

实现比单一 AI 更强健、可扩展的开发工作流。

## 架构亮点

### 多协议支持

| 协议 | 用途 |
|------|------|
| **MCP** (Model Context Protocol) | Agent 间协作工具（任务委托、消息、笔记） |
| **ACP** (Agent Client Protocol) |  Spawn 和管理 Agent 进程（Claude Code, OpenCode, Codex, Gemini） |
| **A2A** (Agent-to-Agent) | 跨平台 Agent 通信的联邦接口 |

### 内置角色

| 角色 | 功能 |
|------|------|
| 🔵 Routa (Coordinator) | 规划工作，将意图解析为结构化 Spec，创建任务，委托给专家 |
| 🟠 CRAFTER (Implementor) | 执行实现任务，写代码，做最小化改动 |
| 🟢 GATE (Verifier) | 审查工作，验证是否符合验收标准，通过或要求修复 |
| 🎯 DEVELOPER (Solo) | 独立规划和实现的单 Agent 模式 |

### 核心功能

- 🔄 **任务编排**：创建任务、委托 Agent、跟踪依赖、并行执行
- 💬 **Agent 间通信**：消息传递、对话历史、完成报告
- 🎯 **技能系统**：OpenCode 兼容的技能发现和动态加载
- 🔌 **ACP 注册表**：从社区安装预配置的 Agent（支持 npx, uvx, 二进制分发）
- 🐙 **GitHub 虚拟工作区**：无需本地 clone，直接浏览和 review GitHub 仓库

### 技术栈

- Tauri (桌面应用)
- Next.js (Web 前端)
- TypeScript
- SQLite / PostgreSQL (可选)

## 部署方式

```bash
# Docker (SQLite)
docker compose up --build

# Docker (PostgreSQL)
docker compose --profile postgres up --build

# CLI
routa -p "Implement feature X"
```

## 与 Agent-Harness 的关联

Routa 采用了与 Agent-Harness 相似的多 Agent 协作思路，但：

- **Routa**：更完整的桌面应用 + Web UI，侧重任务编排和实时协作
- **Agent-Harness**：更轻量，侧重 AI 驱动的自动化测试和验证

两者都支持 MCP/ACP 协议，可考虑将 Routa 作为 Agent-Harness 的 UI 层或任务编排层。

## 参考价值

- 多 Agent 协作的架构参考
- MCP/ACP/A2A 协议的实际应用案例
- 角色分工和任务委托的实现模式
