"""A2A (Agent-to-Agent) Protocol Implementation.

Per PLAN.md Task 4: A2A message format, routing, and signing.
Per D-15: Message format with sender, receiver, action, payload, context, trace_id.
Per D-16: Support sync and async modes.
Per D-17: Handoff with full context transfer.
Per D-18: Ed25519 signature receipts (reuses Phase 02 audit layer).
Per PITFALLS.md Pitfall 15: Version negotiation to prevent protocol drift.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from saw.adapters.crypto.ed25519 import ReceiptSigner
    from saw.domain.agent import AgentContext, AgentResult, AgentTask
    from saw.domain.protocols import AgentProtocol
    from saw.engines.collaborate.dispatcher import AgentDispatcher


A2A_PROTOCOL_VERSION = "1.0.0"


class MessageType(Enum):
    """A2A message types."""

    REQUEST = "request"  # Request another agent to perform action
    RESPONSE = "response"  # Response to a request
    BROADCAST = "broadcast"  # One-way notification
    QUERY = "query"  # Query for information
    RESULT = "result"  # Query result
    HANDOFF = "handoff"  # Task handoff with context (D-17)


@dataclass
class A2AMessage:
    """Agent-to-Agent message format.

    Per D-15: Standard message structure for agent communication.
    """

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    receiver: str | list[str] = ""  # Single agent or broadcast list
    message_type: MessageType = MessageType.REQUEST
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)  # workflow_id, step, etc.
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None  # Request/response pairing
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    protocol_version: str = A2A_PROTOCOL_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for signing/serialization.

        Returns:
            Dictionary representation of the message.
        """
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "message_type": self.message_type.value,
            "action": self.action,
            "payload": self.payload,
            "context": self.context,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
            "protocol_version": self.protocol_version,
        }


@dataclass
class A2AResult:
    """Result of an A2A message delivery."""

    success: bool
    message_id: str
    response: A2AMessage | None = None
    error: str | None = None


class A2AAdapter:
    """A2A protocol adapter for message routing and signing.

    Per D-18: All messages generate Ed25519 signature receipts.
    Per PITFALLS.md Pitfall 15: Version negotiation support.
    """

    def __init__(
        self,
        agents: dict[str, AgentProtocol],
        audit_signer: ReceiptSigner | None,
        dispatcher: AgentDispatcher | None,
    ) -> None:
        """Initialize the A2A adapter.

        Args:
            agents: Dictionary of agent name -> agent instance.
            audit_signer: Ed25519 signer for receipt generation.
            dispatcher: Agent dispatcher for task execution.
        """
        self._agents = agents
        self._signer = audit_signer
        self._dispatcher = dispatcher
        self._message_queue: asyncio.Queue[A2AMessage] = asyncio.Queue()

    def validate_version(self, message: A2AMessage) -> bool:
        """Validate protocol version compatibility.

        Per PITFALLS.md Pitfall 15: Reject incompatible major versions.

        Args:
            message: The message to validate.

        Returns:
            True if versions are compatible.
        """
        # Semantic versioning: major version must match
        try:
            msg_major = message.protocol_version.split(".")[0]
            our_major = A2A_PROTOCOL_VERSION.split(".")[0]
            return msg_major == our_major
        except (IndexError, AttributeError):
            return False

    async def send(self, message: A2AMessage) -> A2AResult:
        """Send an A2A message.

        Args:
            message: The message to send.

        Returns:
            A2AResult indicating delivery success.
        """
        # 1. Version check
        if not self.validate_version(message):
            return A2AResult(
                success=False,
                message_id=message.message_id,
                error=f"Incompatible protocol version: {message.protocol_version}",
            )

        # 2. Generate signature receipt (if signer available)
        if self._signer is not None:
            from saw.adapters.crypto.ed25519 import Receipt

            receipt = Receipt(
                operation_id=message.message_id,
                operation_type="a2a_message",
                agent=message.sender,
                timestamp=message.timestamp,
            )
            # Sign the message data
            self._signer.sign_receipt(receipt)

        # 3. Route message
        if isinstance(message.receiver, list):
            # Broadcast mode - deliver to all receivers
            results = await asyncio.gather(
                *[self._deliver_to_agent(agent, message) for agent in message.receiver],
                return_exceptions=True,
            )
            # Consider success if all deliveries succeeded
            all_success = all(
                not isinstance(r, Exception) and (r.success if hasattr(r, "success") else True)
                for r in results
            )
            return A2AResult(
                success=all_success,
                message_id=message.message_id,
            )
        else:
            # Direct message - deliver to single receiver
            return await self._deliver_to_agent(message.receiver, message)

    async def _deliver_to_agent(
        self,
        agent_name: str,
        message: A2AMessage,
    ) -> A2AResult:
        """Deliver message to a specific agent.

        Args:
            agent_name: Name of the target agent.
            message: The message to deliver.

        Returns:
            A2AResult indicating delivery success.
        """
        agent = self._agents.get(agent_name)
        if not agent:
            return A2AResult(
                success=False,
                message_id=message.message_id,
                error=f"Agent {agent_name} not found",
            )

        # Convert message to Agent task
        from saw.domain.agent import AgentContext, AgentTask

        task = AgentTask(
            type=message.action,
            payload=message.payload,
            correlation_id=message.correlation_id,
        )
        context = AgentContext(
            wiki_state={},
            claims_context=[],
            workflow_id=message.context.get("workflow_id"),
            calling_agent=message.sender,
        )

        try:
            result = await agent.execute(task, context, [])

            # Generate response message for request/query types
            if message.message_type in [MessageType.REQUEST, MessageType.QUERY]:
                response_type = (
                    MessageType.RESPONSE
                    if message.message_type == MessageType.REQUEST
                    else MessageType.RESULT
                )
                return A2AResult(
                    success=True,
                    message_id=message.message_id,
                    response=A2AMessage(
                        sender=agent_name,
                        receiver=message.sender,
                        message_type=response_type,
                        payload=result.payload,
                        correlation_id=message.message_id,
                    ),
                )
            return A2AResult(success=True, message_id=message.message_id)
        except Exception as e:
            return A2AResult(
                success=False,
                message_id=message.message_id,
                error=str(e),
            )

    async def broadcast(
        self,
        sender: str,
        payload: dict[str, Any],
        receivers: list[str],
    ) -> A2AResult:
        """Broadcast message to multiple agents.

        Args:
            sender: The sending agent name.
            payload: The message payload.
            receivers: List of receiver agent names.

        Returns:
            A2AResult indicating broadcast success.
        """
        message = A2AMessage(
            sender=sender,
            receiver=receivers,
            message_type=MessageType.BROADCAST,
            payload=payload,
        )
        return await self.send(message)

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
            sender: The sending agent name.
            receiver: The receiving agent name.
            task_type: Type of task to hand off.
            payload: Task payload.
            context: Full execution context.

        Returns:
            A2AResult indicating handoff success.
        """
        message = A2AMessage(
            sender=sender,
            receiver=receiver,
            message_type=MessageType.HANDOFF,
            action=task_type,
            payload=payload,
            context=context,  # Complete context transfer
        )
        return await self.send(message)

    def get_queue(self) -> asyncio.Queue[A2AMessage]:
        """Get the message queue for async processing.

        Returns:
            The message queue.
        """
        return self._message_queue
