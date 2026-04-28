"""Collaboration engine orchestrator - unified entry point for multi-agent operations.

Per PLAN.md Task 4: CollaborateEngine integrates Dispatcher, A2A, Workflow, Policy.
Provides single interface for agent dispatch, workflow execution, and policy checks.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .a2a_protocol import A2AAdapter, A2AMessage, A2AResult
    from .workflow_executor import WorkflowExecutor, WorkflowResult
    from .workflow_parser import WorkflowDefinition
    from ...adapters.crypto.cedar_policy import PolicyEngine, PolicyDecision
    from ...domain.agent import AgentTask, AgentContext, AgentResult
    from .dispatcher import AgentDispatcher


@dataclass
class CollaborateConfig:
    """Configuration for the collaboration engine.

    Attributes:
        max_concurrent_workflows: Maximum parallel workflow executions
        default_workflow_timeout: Default timeout in seconds
        enable_policy_check: Whether to check Cedar policies before dispatch
    """

    max_concurrent_workflows: int = 5
    default_workflow_timeout: int = 300
    enable_policy_check: bool = True


class CollaborateEngine:
    """Unified entry point for multi-agent collaboration.

    Integrates:
    - AgentDispatcher for model routing
    - A2AAdapter for inter-agent messaging
    - WorkflowExecutor for YAML workflow execution
    - PolicyEngine for Cedar policy checks

    Per D-14: Default deny policy - unpermitted actions are denied.

    Example:
        >>> engine = CollaborateEngine(dispatcher, a2a, workflow, policy)
        >>> result = await engine.execute_workflow(Path("workflow.yaml"), inputs)
        >>> agents = engine.get_available_agents()
    """

    def __init__(
        self,
        dispatcher: AgentDispatcher,
        a2a_adapter: A2AAdapter,
        workflow_executor: WorkflowExecutor,
        policy_engine: PolicyEngine | None = None,
        config: CollaborateConfig | None = None,
    ) -> None:
        """Initialize the collaboration engine.

        Args:
            dispatcher: Agent dispatcher for model routing
            a2a_adapter: A2A adapter for agent messaging
            workflow_executor: Workflow executor for YAML workflows
            policy_engine: Cedar policy engine (optional)
            config: Engine configuration (optional)
        """
        self._dispatcher = dispatcher
        self._a2a = a2a_adapter
        self._workflow = workflow_executor
        self._policy = policy_engine
        self._config = config or CollaborateConfig()

    # === Agent Dispatch ===

    async def dispatch_agent(
        self,
        agent_name: str,
        task: AgentTask,
        context: AgentContext,
        tools: list[Any] | None = None,
        check_policy: bool = True,
    ) -> AgentResult:
        """Dispatch an agent to execute a task.

        Per D-14: Policy check is performed before dispatch unless disabled.

        Args:
            agent_name: Name of the agent to dispatch
            task: Task to execute
            context: Execution context
            tools: Optional list of tools (not used in basic implementation)
            check_policy: Whether to check Cedar policy before dispatch

        Returns:
            AgentResult from the agent execution
        """
        from saw.domain.agent import AgentResult

        # Policy check (per D-14)
        if (
            check_policy
            and self._policy is not None
            and self._config.enable_policy_check
        ):
            decision = self._policy.evaluate(
                principal=f'Agent::"{context.calling_agent or "user"}"',
                action=f'Action::"{task.type}"',
                resource='Resource::"wiki"',
                context={"agent": agent_name},
            )
            if not decision.allowed:
                return AgentResult(
                    success=False,
                    payload={},
                    error=f"Policy denied: {decision.reason}",
                )

        return await self._dispatcher.dispatch(agent_name, task, context, tools)

    # === Workflow Execution ===

    async def execute_workflow(
        self,
        workflow_path: Path,
        inputs: dict[str, Any],
    ) -> WorkflowResult:
        """Execute a YAML workflow file.

        Args:
            workflow_path: Path to workflow YAML file
            inputs: Input context for workflow

        Returns:
            WorkflowResult with execution status and outputs
        """
        return await self._workflow.execute(workflow_path, inputs)

    async def execute_workflow_definition(
        self,
        workflow: WorkflowDefinition,
        inputs: dict[str, Any],
    ) -> WorkflowResult:
        """Execute a pre-parsed workflow definition.

        Args:
            workflow: Parsed workflow definition
            inputs: Input context for workflow

        Returns:
            WorkflowResult with execution status and outputs
        """
        return await self._workflow.execute_definition(workflow, inputs)

    # === A2A Communication ===

    async def send_a2a_message(self, message: A2AMessage) -> A2AResult:
        """Send an A2A message.

        Args:
            message: Message to send

        Returns:
            A2AResult indicating delivery success
        """
        return await self._a2a.send(message)

    async def handoff(
        self,
        sender: str,
        receiver: str,
        task_type: str,
        payload: dict[str, Any],
        context: dict[str, Any],
    ) -> A2AResult:
        """Hand off task to another agent with full context.

        Per D-17: Task handoff includes complete context transfer.

        Args:
            sender: Sending agent name
            receiver: Receiving agent name
            task_type: Type of task to hand off
            payload: Task payload
            context: Full execution context

        Returns:
            A2AResult indicating handoff success
        """
        return await self._a2a.handoff(sender, receiver, task_type, payload, context)

    # === Policy ===

    def check_policy(
        self,
        agent: str,
        action: str,
        resource: str = "wiki",
        context: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        """Check if an agent is authorized to perform an action.

        Per D-14: Default deny - returns allowed=True only if policy engine permits.

        Args:
            agent: Agent name
            action: Action to perform
            resource: Target resource
            context: Optional context for conditional policies

        Returns:
            PolicyDecision with authorization status
        """
        from saw.adapters.crypto.cedar_policy import PolicyDecision

        if self._policy is None:
            return PolicyDecision(allowed=True, reason="No policy engine configured")

        return self._policy.evaluate(
            principal=f'Agent::"{agent}"',
            action=f'Action::"{action}"',
            resource=f'Resource::"{resource}"',
            context=context or {},
        )

    # === Agent Registry ===

    def get_available_agents(self) -> list[str]:
        """Get list of registered agents.

        Returns:
            List of agent names
        """
        return list(self._dispatcher._agents.keys())

    def get_agent_info(self, agent_name: str) -> dict[str, Any] | None:
        """Get information about a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent info dict or None if not found
        """
        agent = self._dispatcher._agents.get(agent_name)
        if agent is None:
            return None

        return {
            "name": agent.name,
            "model_tier": agent.model_tier,
            "tools_allowed": getattr(agent, "_tools_allowed", []),
        }
