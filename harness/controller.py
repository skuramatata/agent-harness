"""
Agent Harness Controller
最小可落地的 Agent 运行框架
"""
import asyncio
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Task:
    id: str
    agent_type: str
    command: str
    timeout: int = 60
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    type: str
    image: str
    tools: List[str]
    replicas: int = 1
    timeout: int = 300
    max_concurrent: int = 1


class AgentPod:
    """Agent 容器实例"""
    
    def __init__(self, agent_type: str, config: AgentConfig):
        self.id = f"{agent_type}-{uuid.uuid4()[:8]}"
        self.agent_type = agent_type
        self.config = config
        self._current_tasks = 0
        self._available = True
    
    def is_available(self) -> bool:
        return self._available and self._current_tasks < self.config.max_concurrent
    
    async def start(self):
        logger.info(f"Starting agent pod: {self.id}")
        # 这里启动实际的容器
        self._available = True
    
    async def stop(self):
        logger.info(f"Stopping agent pod: {self.id}")
        self._available = False
    
    async def execute(self, command: str, timeout: int) -> str:
        """执行命令"""
        self._current_tasks += 1
        try:
            logger.info(f"Executing command on {self.id}: {command}")
            
            # 创建子进程执行命令
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
                result = stdout.decode() if stdout else stderr.decode()
                logger.info(f"Command completed on {self.id}")
                return result
            except asyncio.TimeoutError:
                proc.kill()
                raise TimeoutError(f"Command timed out after {timeout}s")
        finally:
            self._current_tasks -= 1


class HarnessController:
    """Harness 控制器"""
    
    def __init__(self, configs: List[AgentConfig]):
        self.configs = configs
        self.agents: Dict[str, AgentPod] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue = asyncio.Queue()
        self._running = False
    
    async def start(self):
        """启动 Controller"""
        logger.info("Starting Harness Controller...")
        self._running = True
        
        # 初始化 Agent Pool
        for config in self.configs:
            for i in range(config.replicas):
                agent = AgentPod(config.type, config)
                await agent.start()
                self.agents[agent.id] = agent
                logger.info(f"Created agent: {agent.id}")
        
        # 启动任务处理循环
        asyncio.create_task(self._process_tasks())
        logger.info(f"Harness Controller started with {len(self.agents)} agents")
    
    async def stop(self):
        """停止 Controller"""
        logger.info("Stopping Harness Controller...")
        self._running = False
        
        for agent in self.agents.values():
            await agent.stop()
        
        logger.info("Harness Controller stopped")
    
    async def submit_task(
        self, 
        agent_type: str, 
        command: str, 
        timeout: int = 60,
        metadata: Dict[str, Any] = None
    ) -> str:
        """提交任务"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            agent_type=agent_type,
            command=command,
            timeout=timeout,
            metadata=metadata or {}
        )
        self.tasks[task_id] = task
        await self.task_queue.put(task)
        logger.info(f"Task {task_id} submitted to {agent_type}")
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    async def _process_tasks(self):
        """任务处理循环"""
        while self._running:
            task = await self.task_queue.get()
            asyncio.create_task(self._execute_task(task))
    
    async def _execute_task(self, task: Task):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        
        # 查找可用 Agent
        agent = self._get_available_agent(task.agent_type)
        if not agent:
            task.status = TaskStatus.FAILED
            task.error = "No available agent"
            logger.error(f"Task {task.id} failed: No available agent")
            return
        
        try:
            result = await agent.execute(task.command, task.timeout)
            task.result = result
            task.status = TaskStatus.COMPLETED
            logger.info(f"Task {task.id} completed")
        except TimeoutError as e:
            task.error = str(e)
            task.status = TaskStatus.TIMEOUT
            logger.error(f"Task {task.id} timed out")
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            logger.error(f"Task {task.id} failed: {e}")
    
    def _get_available_agent(self, agent_type: str) -> Optional[AgentPod]:
        """获取可用 Agent"""
        for agent in self.agents.values():
            if agent.agent_type == agent_type and agent.is_available():
                return agent
        return None
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有 Agent"""
        return [
            {
                "id": agent.id,
                "type": agent.agent_type,
                "available": agent.is_available(),
                "current_tasks": agent._current_tasks
            }
            for agent in self.agents.values()
        ]


async def main():
    """示例入口"""
    configs = [
        AgentConfig(
            type="coding-agent",
            image="openclaw/coding-agent:latest",
            tools=["read", "write", "exec"],
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
    
    # 提交测试任务
    task_id = await controller.submit_task(
        agent_type="coding-agent",
        command="echo 'Hello from agent!'",
        timeout=10
    )
    
    # 等待任务完成
    await asyncio.sleep(2)
    
    # 获取结果
    task = await controller.get_task(task_id)
    print(f"Task {task.id}: {task.status.value}")
    print(f"Result: {task.result}")
    
    # 列出 Agents
    print("\nAgents:")
    for agent in controller.list_agents():
        print(f"  {agent}")
    
    await controller.stop()


if __name__ == "__main__":
    asyncio.run(main())
