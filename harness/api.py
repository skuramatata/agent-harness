"""
Harness API Server
基于 FastAPI 的 REST API
"""
import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from controller import HarnessController, AgentConfig, TaskStatus


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8080


settings = Settings()

# 全局 Controller
controller: Optional[HarnessController] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global controller
    
    # 启动时初始化
    configs = [
        AgentConfig(
            type="coding-agent",
            image="openclaw/coding-agent:latest",
            tools=["read", "write", "exec", "browser"],
            replicas=2,
            timeout=300
        ),
        AgentConfig(
            type="research-agent",
            image="openclaw/research-agent:latest",
            tools=["web_search", "web_fetch"],
            replicas=1,
            timeout=120
        )
    ]
    
    controller = HarnessController(configs)
    await controller.start()
    
    yield
    
    # 关闭时清理
    await controller.stop()


app = FastAPI(title="Agent Harness API", lifespan=lifespan)


# --- Models ---

class TaskSubmit(BaseModel):
    agent_type: str
    command: str
    timeout: Optional[int] = 60
    metadata: Optional[dict] = None


class TaskResponse(BaseModel):
    id: str
    agent_type: str
    command: str
    timeout: int
    status: str
    result: Optional[str] = None
    error: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    type: str
    available: bool
    current_tasks: int


# --- Routes ---

@app.get("/")
async def root():
    return {"status": "ok", "service": "agent-harness"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/v1/tasks", response_model=dict)
async def submit_task(task: TaskSubmit):
    """提交任务"""
    task_id = await controller.submit_task(
        agent_type=task.agent_type,
        command=task.command,
        timeout=task.timeout,
        metadata=task.metadata
    )
    return {"task_id": task_id, "status": "submitted"}


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """获取任务状态"""
    task = await controller.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(
        id=task.id,
        agent_type=task.agent_type,
        command=task.command,
        timeout=task.timeout,
        status=task.status.value,
        result=task.result,
        error=task.error
    )


@app.get("/api/v1/agents", response_model=List[AgentResponse])
async def list_agents():
    """列出所有 Agent"""
    return [AgentResponse(**a) for a in controller.list_agents()]


@app.post("/api/v1/agents/{agent_id}/stop")
async def stop_agent(agent_id: str):
    """停止 Agent"""
    agent = controller.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await agent.stop()
    return {"status": "stopped", "agent_id": agent_id}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
