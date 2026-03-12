# Agent Harness 最小可落地方案

## 什么是 Agent Harness

Agent Harness = Agent 运行沙箱 + 通信协议 + 任务编排

核心目标：让 AI Agent 安全、可控、可扩展地执行任务。

---

## 最小可行架构 (MVP)

```
┌─────────────────────────────────────────────────┐
│                  Gateway (API)                   │
│              (OpenClaw Gateway)                  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Harness Controller                   │
│  - 任务分发 (Task Distribution)                   │
│  - 状态管理 (State Management)                    │
│  - 生命周期 (Lifecycle)                           │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│  Agent Pod A  │   │  Agent Pod B  │
│  - 隔离环境    │   │  - 隔离环境    │
│  - 工具权限   │   │  - 工具权限   │
│  - 会话管理   │   │  - 会话管理   │
└───────────────┘   └───────────────┘
```

---

## 核心组件

### 1. Harness Controller (Python/Go)

```python
class AgentHarness:
    def __init__(self, config):
        self.agents = {}  # agent_id -> agent
        self.tasks = {}   # task_id -> task_state
    
    async def spawn_agent(self, agent_type, config):
        # 创建隔离的 Agent 实例
        agent = await AgentFactory.create(agent_type, config)
        self.agents[agent.id] = agent
        return agent
    
    async def submit_task(self, agent_id, task):
        # 提交任务到指定 Agent
        agent = self.agents[agent_id]
        return await agent.execute(task)
    
    async def get_result(self, task_id):
        # 获取任务结果
        return self.tasks[task_id].result
```

### 2. Agent Pod (隔离环境)

- 独立的进程/容器
- 有限制的工具权限
- 会话状态隔离
- 超时控制

### 3. 通信协议 (ACP)

```json
{
  "version": "1.0",
  "task_id": "task_123",
  "agent_id": "agent_456",
  "action": "execute",
  "payload": {
    "command": "ls -la",
    "timeout": 30
  },
  "metadata": {
    "user": "user_789",
    "priority": "normal"
  }
}
```

---

## 快速启动 (3 步)

### Step 1: 定义 Agent 配置

```yaml
# agent-config.yaml
agents:
  - id: coding-agent
    image: openclaw/coding-agent:latest
    tools:
      - read
      - write
      - exec
    timeout: 300
    max_concurrent: 3
  
  - id: research-agent
    image: openclaw/research-agent:latest
    tools:
      - web_search
      - web_fetch
    timeout: 120
    max_concurrent: 5
```

### Step 2: 启动 Harness

```bash
# 使用 Docker Compose
docker-compose up -d harness-controller

# 或直接运行
python -m harness.controller --config agent-config.yaml
```

### Step 3: 调用 API

```bash
# 提交任务
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "coding-agent",
    "command": "帮我写一个 hello world"
  }'

# 获取结果
curl http://localhost:8080/api/v1/tasks/{task_id}
```

---

## 最小功能清单

| 功能 | 优先级 | 说明 |
|------|--------|------|
| Agent 生命周期管理 | P0 | 启动/停止/重启 |
| 任务提交与结果获取 | P0 | 同步/异步 |
| 工具权限控制 | P0 | 白名单机制 |
| 超时控制 | P0 | 防止无限运行 |
| 日志收集 | P1 | 任务日志/错误日志 |
| 并发控制 | P1 | 资源限制 |
| 健康检查 | P2 | Agent 状态监控 |

---

## 技术选型

| 组件 | 推荐方案 | 理由 |
|------|----------|------|
| 容器运行时 | Docker | 成熟、生态丰富 |
| 任务队列 | Redis / 内存 | 简单够用 |
| API 网关 | OpenClaw Gateway | 已有基础设施 |
| 状态存储 | SQLite / Redis | 轻量 |
| 监控 | Prometheus (可选) | 扩展性 |

---

## 风险与限制

1. **安全隔离**：容器级隔离，非真正沙箱
2. **资源控制**：需配合 cgroup/ulimit
3. **状态持久化**：当前方案为内存存储，需外置 DB
4. **扩展性**：单节点方案，多节点需引入 K8s

---

## 下一步

1. 先跑通单机版 Agent Pod
2. 实现基础的 Task Queue
3. 接入 OpenClaw Gateway 作为 API 层
4. 添加监控与日志

---

*Created: 2026-03-12*
