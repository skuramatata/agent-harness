# Agent Harness MVP

最小可落地的 Agent 运行框架。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Gateway (API)                          │
│                    OpenClaw Gateway                         │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Harness Controller                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Task Queue  │  │Agent Manager│  │  State Store│       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Agent Pod A  │  │  Agent Pod B  │  │  Agent Pod C  │
│  - 隔离容器    │  │  - 隔离容器    │  │  - 隔离容器    │
│  - 工具白名单  │  │  - 工具白名单  │  │  - 工具白名单  │
│  - 超时控制   │  │  - 超时控制   │  │  - 超时控制   │
└───────────────┘  └───────────────┘  └───────────────┘
```

## 快速开始

### 1. 启动 Harness Controller

```bash
docker run -p 8080:8080 \
  -v ./config.yaml:/app/config.yaml \
  openclaw/harness-controller:latest
```

### 2. 提交任务

```bash
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "coding-agent",
    "command": "写一个 hello world",
    "timeout": 60
  }'
```

### 3. 获取结果

```bash
curl http://localhost:8080/api/v1/tasks/{task_id}
```

## 核心代码

### Harness Controller

```python
# harness/controller.py
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    id: str
    agent_type: str
    command: str
    timeout: int = 60
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None

class AgentHarness:
    def __init__(self, config: dict):
        self.config = config
        self.agents: Dict[str, 'AgentPod'] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue = asyncio.Queue()
    
    async def start(self):
        """启动 Controller"""
        # 初始化 Agent Pool
        for agent_config in self.config.get('agents', []):
            for _ in range(agent_config.get('replicas', 1)):
                agent = AgentPod(agent_config)
                await agent.start()
                self.agents[agent.id] = agent
        
        # 启动任务处理循环
        asyncio.create_task(self._process_tasks())
    
    async def submit_task(self, agent_type: str, command: str, timeout: int = 60) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            agent_type=agent_type,
            command=command,
            timeout=timeout
        )
        self.tasks[task_id] = task
        await self.task_queue.put(task)
           async def _ return task_id
    
process_tasks(self):
        """任务处理循环"""
        while True:
            task = await self.task_queue.get()
            asyncio.create_task(self._execute_task(task))
    
    async def _execute_task(self, task: Task):
        """执行任务"""
        task.status = TaskStatus.Running
        
        # 查找可用 Agent
        agent = self._get_available_agent(task.agent_type)
        if not agent:
            task.status = TaskStatus.FAILED
            task.error = "No available agent"
            return
        
        try:
            result = await agent.execute(task.command, task.timeout)
            task.result = result
            task.status = TaskStatus.COMPLETED
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
    
    def _get_available_agent(self, agent_type: str) -> Optional['AgentPod']:
        """获取可用 Agent"""
        for agent in self.agents.values():
            if agent.agent_type == agent_type and agent.is_available():
                return agent
        return None
```

### Agent Pod

```python
# harness/agent_pod.py
import asyncio
import subprocess
from dataclasses import dataclass
from typing import List, Optional
import uuid

@dataclass
class AgentPod:
    id: str
    agent_type: str
    tools: List[str]
    max_concurrent: int = 1
    timeout: int = 300
    
    _current_tasks: int = 0
    _process: Optional[subprocess.Process] = None
    
    def __post_init__(self):
        self.id = f"{self.agent_type}-{uuid.uuid4()[:8]}"
    
    def is_available(self) -> bool:
        return self._current_tasks < self.max_concurrent
    
    async def start(self):
        """启动 Agent 容器"""
        # 这里启动实际的容器或进程
        pass
    
    async def execute(self, command: str, timeout: int) -> str:
        """执行命令"""
        self._current_tasks += 1
        try:
            # 执行命令（模拟）
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                return stdout.decode() if stdout else stderr.decode()
            except asyncio.TimeoutError:
                proc.kill()
                raise TimeoutError(f"Command timed out after {timeout}s")
        finally:
            self._current_tasks -= 1
```

### ACP 协议

```json
{
  "version": "1.0",
  "task_id": "task_abc123",
  "agent_id": "agent_xyz789",
  "action": "execute",
  "payload": {
    "command": "ls -la",
    "timeout": 30,
    "tools": ["read", "write", "exec"]
  },
  "metadata": {
    "user_id": "user_123",
    "priority": "normal",
    "created_at": "2026-03-12T02:58:00Z"
  }
}
```

## 配置示例

```yaml
# config.yaml
harness:
  port: 8080
  
agents:
  - type: coding-agent
    image: openclaw/coding-agent:latest
    replicas: 3
    tools:
      - read
      - write
      - exec
      - browser
    timeout: 300
    resources:
      cpu: "1000m"
      memory: "1Gi"
  
  - type: research-agent
    image: openclaw/research-agent:latest
    replicas: 2
    tools:
      - web_search
      - web_fetch
    timeout: 120

security:
  tool_whitelist: true
  max_concurrent_per_user: 3
  default_timeout: 60
```

## API

| Method | Path | 说明 |
|--------|------|------|
| POST | /api/v1/tasks | 提交任务 |
| GET | /api/v1/tasks/{id} | 获取任务状态 |
| GET | /api/v1/agents | 列出 Agent |
| POST | /api/v1/agents/{id}/stop | 停止 Agent |

## 下一步

- [ ] 实现真正的容器隔离
- [ ] 添加 WebSocket 支持
- [ ] 集成 Prometheus 监控
- [ ] 支持多节点部署

---

MIT License
